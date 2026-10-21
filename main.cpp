#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <thread>
#include <chrono>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netinet/if_ether.h>
#include <arpa/inet.h>
#include <unistd.h>
using namespace std;

class NetworkMonitor {
public:
//Monitoring RAM//////////////////
long long getValue(const string& key) {
    ifstream file("/proc/meminfo");
    string line;

    while (getline(file, line)) {
        if (line.find(key) != string::npos) {
            //extract number
            string label;
            long long value;
            string unit;

            stringstream ss(line);
            ss >> label >> value >> unit;

            return value; //in KBs
        }
    }

    return -1;
}
void printMemoryLive(){
 while (true) {
        long long memTotal = getValue("MemTotal");
        long long memFree = getValue("MemAvailable");

        long long used = memTotal - memFree;

        double usedGB = used / 1024.0 / 1024.0;
        double totalGB = memTotal / 1024.0 / 1024.0;

        system("clear"); //so we update the value each time

        cout << "=== LIVE MEMORY MONITOR ===\n";
        cout << "Total RAM: " << totalGB << " GB\n";
        cout << "Used RAM : " << usedGB << " GB\n";
        cout << "Free RAM : " << (memFree / 2048.0 ) << " GB\n";

        this_thread::sleep_for(chrono::seconds(1));
    }
}
//////////////////////////////////////////////////////////////////

//Monitoring Packet Stats/////////////////////////////////////////
int printPacketsLive() {
        int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

        if (sock < 0) {
            perror("Socket Error");
            return 1;
        }

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

            cout << "Source IP: " << inet_ntoa(src.sin_addr)
                 << " | Destination IP: " << inet_ntoa(dest.sin_addr)
                 << " | Protocol: ";

            if (ip->protocol == IPPROTO_TCP) {
                struct tcphdr* tcp = (struct tcphdr*)(buffer + sizeof(struct ethhdr) + ip->ihl * 4);

                cout << "TCP"
                     << " | Source Port: " << ntohs(tcp->source)
                     << " | Destination Port: " << ntohs(tcp->dest)
                     << " | Packet Size: " << size
                     << endl;
            }
            else if (ip->protocol == IPPROTO_UDP) {
                struct udphdr* udp = (struct udphdr*)(buffer + sizeof(struct ethhdr) + ip->ihl * 4);

                cout << "UDP"
                     << " | Source Port: " << ntohs(udp->source)
                     << " | Destination Port: " << ntohs(udp->dest)
                     << " | Packet Size: " << size
                     << endl;
            }
            else {
                cout << "Other"
                     << " | Packet Size: " << size
                     << endl;
            }
        }

        close(sock);
        return 0;
    }


//////////////////////////////////////////////////////////////////
};


int main() {

NetworkMonitor S;
S.printPacketsLive();

    return 0;
}