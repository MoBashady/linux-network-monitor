#include <iostream>
#include <fstream>
#include <string>
#include <pwd.h>
#include <sys/types.h>
using namespace std;

string getUserFromPID(int pid) {
    string path = "/proc/" + to_string(pid) + "/status";
    ifstream file(path);
    if (!file.is_open()) return "Unknown";

    string line;
    while (std::getline(file, line)) {
        if (line.rfind("Uid:", 0) == 0) {
            int uid = std::stoi(line.substr(5));
            struct passwd *pw = getpwuid(uid);
            return pw ? pw->pw_name : "Unknown";
        }
    }
    return "Unknown";
}

int main() {
    int pid;
    std::cout << "Enter PID: ";
    std::cin >> pid;
    std::cout << "Owner: " << getUserFromPID(pid) << std::endl;
    return 0;
}
