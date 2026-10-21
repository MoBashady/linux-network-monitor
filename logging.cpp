#include <iostream>
#include <fstream>
#include <ctime>
#include <string>

using namespace std;

class LoggingModule {
private:
    ofstream logFile;

public:
    LoggingModule(const string& filename = "network_log.txt") {
        logFile.open(filename, ios::app);
    }

    ~LoggingModule() {
        if (logFile.is_open())
            logFile.close();
    }

    string getTimestamp() {
        time_t now = time(0);
        char* dt = ctime(&now);
        string timestamp(dt);
        timestamp.pop_back();
        return timestamp;
    }

    void logPacket(const string& srcIP, const string& destIP,
                   const string& protocol, int srcPort,
                   int destPort, int packetSize) {
        if (!logFile.is_open()) return;

        logFile << "[" << getTimestamp() << "] "
                << "Source IP: " << srcIP
                << " | Destination IP: " << destIP
                << " | Protocol: " << protocol
                << " | Source Port: " << srcPort
                << " | Destination Port: " << destPort
                << " | Packet Size: " << packetSize
                << endl;
    }
};