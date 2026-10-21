#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <dirent.h>
#include <unistd.h>

using namespace std;

string getinode(int target) {
    ifstream file("/proc/net/tcp");
    string line;
    getline(file, line); // skip header

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

        string hexPort = localAddr.substr(localAddr.find(':') + 1);
        int port = stoi(hexPort, nullptr, 16);

        if (port == target)
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

int main() {
    int port;
    cout << "Enter port: ";
    cin >> port;

    string inode = getinode(port);
    if (inode.empty()) {
        cout << "No socket found\n";
        return 0;
    }

    cout << "Found inode: " << inode << endl;

    int pid = getPID(inode);
    if (pid == -1)
        cout << "No process found\n";
    else
        cout << "PID: " << pid << endl;

    return 0;
}