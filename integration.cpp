#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <thread>
#include <chrono>
#include <pwd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/if_ether.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <vector>
#include <ctime>
#include <dirent.h>

using namespace std;

struct PacketInfo {
    string srcIP = "";
    string destIP = "";
    string protocol = "Unknown";
    int srcPort = 0;
    int destPort = 0;
    int packetSize = 0;
    int pid = -1;
    string user = "Unknown";
    string process = "unknown";
};

class NetworkMonitor {
public:
       long long getValue(const string& key) {
        ifstream file("/proc/meminfo");
        string line;

        while (getline(file, line)) {
            if (line.find(key) != string::npos) {
                string label;
                long long value;
                string unit;

                stringstream ss(line);
                ss >> label >> value >> unit;

                return value;
            }
        }

        return -1;
    }

    void printMemoryLive() {
        while (true) {
            long long memTotal = getValue("MemTotal");
            long long memAvailable = getValue("MemAvailable");

            long long used = memTotal - memAvailable;

            double usedGB = used / 1024.0 / 1024.0;
            double totalGB = memTotal / 1024.0 / 1024.0;
            double freeGB = memAvailable / 1024.0 / 1024.0;

            system("clear");

            cout << "=== LIVE MEMORY MONITOR ===\n";
            cout << "Total RAM: " << totalGB << " GB\n";
            cout << "Used RAM : " << usedGB << " GB\n";
            cout << "Free RAM : " << freeGB << " GB\n";

            this_thread::sleep_for(chrono::seconds(1));
        }
    }

    int openSocket() {
        int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
        if (sock < 0) {
            perror("Socket Error");
        }   
        return sock;
    }

    string searchInodeInFile(const string& path, int targetPort) {
        ifstream file(path);
        if (!file.is_open()) return "";

        string line;
        getline(file, line); 

        while (getline(file, line)) {
            istringstream iss(line);
            vector<string> fields;
            string field;

            while (iss >> field) {
                fields.push_back(field);
            }

            if (fields.size() < 10) continue;

            string localAddr = fields[1];
            string inode = fields[9];

            size_t colonPos = localAddr.find(':');
            if (colonPos == string::npos) continue;

            string hexPort = localAddr.substr(colonPos + 1);
            int port = stoi(hexPort, nullptr, 16);

            if (port == targetPort)
                return inode;
        }

        return "";
    }

    string getProcessNameFromPID(int pid) {
        string path = "/proc/" + to_string(pid) + "/comm";
        ifstream file(path);
        if (!file.is_open()) return "unknown";

        string processName;
        getline(file, processName);

        if (processName.empty()) return "unknown";
        return processName;
    }

    string getinode(int targetPort, const string& protocol) {
    string inode;

    if (protocol == "TCP") {
        inode = searchInodeInFile("/proc/net/tcp", targetPort);
        if (!inode.empty()) return inode;

        inode = searchInodeInFile("/proc/net/tcp6", targetPort);
        return inode;
    }

    if (protocol == "UDP") {
        inode = searchInodeInFile("/proc/net/udp", targetPort);
        if (!inode.empty()) return inode;

        inode = searchInodeInFile("/proc/net/udp6", targetPort);
        return inode;
    }

    return "";
}
    
    int getPID(const string& inode) {
        DIR* procDir = opendir("/proc");
        if (!procDir) return -1;

        dirent* procEntry;
        while ((procEntry = readdir(procDir)) != nullptr) {
            if (!isdigit(procEntry->d_name[0])) continue;

            string pid = procEntry->d_name;
            string fdPath = "/proc/" + pid + "/fd";
            DIR* fdDir = opendir(fdPath.c_str());
            if (!fdDir) continue;

            dirent* fdEntry;
            char link[256];

        while ((fdEntry = readdir(fdDir)) != nullptr) {
            string fullPath = fdPath + "/" + fdEntry->d_name;
            ssize_t len = readlink(fullPath.c_str(), link, sizeof(link) - 1);

            if (len != -1) {
                link[len] = '\0';
                if (string(link) == "socket:[" + inode + "]") {
                    closedir(fdDir);
                    closedir(procDir);
                    return stoi(pid);
                }
            }
        }
        closedir(fdDir);
    }

        closedir(procDir);
        return -1;
    }

    string getUserFromPID(int pid) {
    string path = "/proc/" + to_string(pid) + "/status";
    ifstream file(path);
    if (!file.is_open()) return "Unknown";

    string line;
    while (getline(file, line)) {
        if (line.rfind("Uid:", 0) == 0) {
            int uid = stoi(line.substr(5));
            struct passwd* pw = getpwuid(uid);
            return pw ? pw->pw_name : "Unknown";
        }
    }
    return "Unknown";
}

    PacketInfo captureAndTrackPacket(int sock) {
        PacketInfo info;

        char buffer[65536];

        while (true) {
            ssize_t size = recvfrom(sock, buffer, sizeof(buffer), 0, nullptr, nullptr);

            if (size < 0) {
                perror("Receive Error");
                break;
            }

            struct ethhdr* eth = (struct ethhdr*)buffer;

            if (ntohs(eth->h_proto) != ETH_P_IP)
                continue;

            struct iphdr* ip = (struct iphdr*)(buffer + sizeof(struct ethhdr));

            struct sockaddr_in src, dest;
            src.sin_addr.s_addr = ip->saddr;
            dest.sin_addr.s_addr = ip->daddr;

            info.srcIP = inet_ntoa(src.sin_addr);
            info.destIP = inet_ntoa(dest.sin_addr);
            info.packetSize = size;

            if (ip->protocol == IPPROTO_TCP) {
                struct tcphdr* tcp = (struct tcphdr*)(buffer + sizeof(struct ethhdr) + ip->ihl * 4);

                info.protocol = "TCP";
                info.srcPort = ntohs(tcp->source);
                info.destPort = ntohs(tcp->dest);
            }
            else if (ip->protocol == IPPROTO_UDP) {
                struct udphdr* udp = (struct udphdr*)(buffer + sizeof(struct ethhdr) + ip->ihl * 4);

                info.protocol = "UDP";
                info.srcPort = ntohs(udp->source);
                info.destPort = ntohs(udp->dest);
            }
            else {
                info.protocol = "Other";
                info.srcPort = 0;
                info.destPort = 0;
            }
            string inode = getinode(info.srcPort, info.protocol);

            if (inode.empty()) {
                inode = getinode(info.destPort, info.protocol);
            }

            if (!inode.empty()) {
                info.pid = getPID(inode);
                if (info.pid != -1) {
                    info.user = getUserFromPID(info.pid);
                    info.process = getProcessNameFromPID(info.pid);
                }
            }

            break;
        }

        return info;
    }


};

class StatisticsModule {
    private:
        long long totalPackets = 0;
        long long totalBytes = 0;
        long long tcpPackets = 0;
        long long udpPackets = 0;
        long long otherPackets = 0;
        long long tcpBytes = 0;
        long long udpBytes = 0;
        long long otherBytes = 0;

    public:

    void addPacket(const PacketInfo& p) {
        totalPackets++;
        totalBytes += p.packetSize;

        if (p.protocol == "TCP") {
            tcpPackets++;
            tcpBytes += p.packetSize;
        } else if (p.protocol == "UDP") {
            udpPackets++;
            udpBytes += p.packetSize;
        } else {
            otherPackets++;
            otherBytes += p.packetSize;
        }
    }

     void printStats() {
        double avgPacketSize = (totalPackets > 0) ? (double)totalBytes / totalPackets : 0;
        double tcpPercent = (totalPackets > 0) ? (double)tcpPackets * 100 / totalPackets : 0;
        double udpPercent = (totalPackets > 0) ? (double)udpPackets * 100 / totalPackets : 0;
        double otherPercent = (totalPackets > 0) ? (double)otherPackets * 100 / totalPackets : 0;

        cout << "\n=== Traffic Statistics ===\n";
        cout << "Total Packets   : " << totalPackets << endl;
        cout << "Total Bytes     : " << totalBytes << endl;
        cout << "TCP Packets     : " << tcpPackets << endl;
        cout << "UDP Packets     : " << udpPackets << endl;
        cout << "Other Packets   : " << otherPackets << endl;
        cout << "TCP Bytes       : " << tcpBytes << endl;
        cout << "UDP Bytes       : " << udpBytes << endl;
        cout << "Other Bytes     : " << otherBytes << endl;
        cout << "Average Pkt Size: " << avgPacketSize << " bytes" << endl;
        cout << "TCP %           : " << tcpPercent << "%" << endl;
        cout << "UDP %           : " << udpPercent << "%" << endl;
        cout << "Other %         : " << otherPercent << "%" << endl;
    }
};

class LoggingModule {
private:
    ofstream logFile;

public:
    LoggingModule(const string& filename = "network_log.jsonl") {
        logFile.open(filename, ios::app);
    }

    ~LoggingModule() {
        if (logFile.is_open())
            logFile.close();
    }


    void logPacket(const PacketInfo& p) {
    if (!logFile.is_open()) return;

    time_t now = time(0);
    tm* lt = localtime(&now);

    char timeBuf[9];
    strftime(timeBuf, sizeof(timeBuf), "%H:%M:%S", lt);

    logFile << "{"
            << "\"timestamp\":\"" << timeBuf << "\","
            << "\"process\":\"" << p.process << "\","
            << "\"pid\":" << p.pid << ","
            << "\"user\":\"" << p.user << "\","
            << "\"bytes_sent\":" << p.packetSize << ","
            << "\"bytes_received\":0,"
            << "\"protocol\":\"" << p.protocol << "\","
            << "\"remote_ip\":\"" << p.destIP << "\""
            << "}" << endl;
    }   
};

int main() {
    NetworkMonitor S;
    StatisticsModule stats;
    LoggingModule logger;

    int sock = S.openSocket();
    if (sock < 0) return 1;

    while (true) {
        PacketInfo p = S.captureAndTrackPacket(sock);
        if (p.protocol == "Unknown") continue;

        stats.addPacket(p);
        logger.logPacket(p);

        this_thread::sleep_for(chrono::milliseconds(50));
    }

    close(sock);
    return 0;
}
