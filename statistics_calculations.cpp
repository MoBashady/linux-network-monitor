#include <iostream>
using namespace std;

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

    void addPacket(int protocol, int packetSize) {
        totalPackets++;
        totalBytes += packetSize;

        if (protocol == 6) {
            tcpPackets++;
            tcpBytes += packetSize;
        } else if (protocol == 17) {
            udpPackets++;
            udpBytes += packetSize;
        } else {
            otherPackets++;
            otherBytes += packetSize;
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