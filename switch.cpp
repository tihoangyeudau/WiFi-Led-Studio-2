#include <windows.h>
#include <tlhelp32.h>
#include <iostream>
#include <string>
#include <stdexcept>

// Hàm m? r?ng bi?n môi tru?ng
std::string ExpandEnvironmentVariables(const std::string& str) {
    DWORD size = ExpandEnvironmentStrings(str.c_str(), NULL, 0);
    if (size == 0) {
        throw std::runtime_error("Failed to expand environment strings");
    }
    std::string result(size, '\0');
    if (ExpandEnvironmentStrings(str.c_str(), &result[0], size) == 0) {
        throw std::runtime_error("Failed to expand environment strings");
    }
    result.resize(size - 1); // Xóa ký t? null k?t thúc chu?i
    return result;
}

// Hàm ki?m tra ti?n trình dang ch?y
bool IsProcessRunning(const std::string& processName) {
    bool exists = false;
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32 pe;
        pe.dwSize = sizeof(PROCESSENTRY32);
        if (Process32First(hSnap, &pe)) {
            do {
                if (std::string(pe.szExeFile) == processName) {
                    exists = true;
                    break;
                }
            } while (Process32Next(hSnap, &pe));
        }
        CloseHandle(hSnap);
    }
    return exists;
}

// Hàm ch? ti?n trình thoát
void WaitForProcessExit(const std::string& processName) {
    while (IsProcessRunning(processName)) {
        Sleep(1000); // Ch? 1 giây tru?c khi ki?m tra l?i
    }
}

int main() {
    try {
        std::cout << "Checking if WiFi Led Studio.exe is running..." << std::endl;

        // Ki?m tra ti?n trình WiFi Led Studio.exe
        if (IsProcessRunning("WiFi Led Studio.exe")) {
            std::cout << "WiFi Led Studio.exe is running. Waiting for it to exit..." << std::endl;
            WaitForProcessExit("WiFi Led Studio.exe");
            std::cout << "WiFi Led Studio.exe has exited." << std::endl;
        } else {
            std::cout << "WiFi Led Studio.exe is not running." << std::endl;
        }

        // Ðu?ng d?n tuong d?i d?n ?ng d?ng ambilightwifi.exe
        std::string ambilightRelative = "%ProgramFiles%\\Ambilight WiFi-USB\\bin\\ambilightwifi.exe";

        // M? r?ng du?ng d?n thành du?ng d?n tuy?t d?i
        std::string ambilightApp = ExpandEnvironmentVariables(ambilightRelative);

        // T?o ti?n trình ambilightwifi.exe
        STARTUPINFO siAmbilight;
        PROCESS_INFORMATION piAmbilight;
        ZeroMemory(&siAmbilight, sizeof(siAmbilight));
        siAmbilight.cb = sizeof(siAmbilight);
        ZeroMemory(&piAmbilight, sizeof(piAmbilight));

        if (!CreateProcess(NULL, const_cast<char*>(ambilightApp.c_str()), NULL, NULL, FALSE, 0, NULL, NULL, &siAmbilight, &piAmbilight)) {
            std::cerr << "Failed to start ambilightwifi.exe: " << GetLastError() << std::endl;
            return 1;
        }

        std::cout << "Started ambilightwifi.exe." << std::endl;

        // Ðóng các handle cho ti?n trình ambilightwifi.exe
        CloseHandle(piAmbilight.hProcess);
        CloseHandle(piAmbilight.hThread);

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}

