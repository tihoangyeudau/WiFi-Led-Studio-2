#include <windows.h>
#include <tlhelp32.h>
#include <iostream>
#include <string>

bool isProcessRunning(const wchar_t* processName) {
    bool exists = false;
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return false;

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (wcscmp(pe.szExeFile, processName) == 0) {
                exists = true;
                break;
            }
        } while (Process32NextW(hSnap, &pe));
    }

    CloseHandle(hSnap);
    return exists;
}

void terminateProcess(const wchar_t* processName) {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return;

    PROCESSENTRY32W pe;
    pe.dwSize = sizeof(PROCESSENTRY32W);

    if (Process32FirstW(hSnap, &pe)) {
        do {
            if (wcscmp(pe.szExeFile, processName) == 0) {
                HANDLE hProc = OpenProcess(PROCESS_TERMINATE, FALSE, pe.th32ProcessID);
                if (hProc != NULL) {
                    TerminateProcess(hProc, 0);
                    CloseHandle(hProc);
                    break; // Assuming only one instance running, exit loop after terminating
                }
            }
        } while (Process32NextW(hSnap, &pe));
    }

    CloseHandle(hSnap);
}

int main() {
    wchar_t appPath[MAX_PATH];
    ExpandEnvironmentStringsW(L"%ProgramFiles%\\WiFi Led Studio\\WiFi Led Studio.exe", appPath, MAX_PATH);

    // Kết thúc tiến trình ambilightwifi.exe nếu nó đang chạy
    terminateProcess(L"WiFi Led Studio.exe");

    // Đợi cho đến khi ambilightwifi.exe thực sự đã kết thúc
    while (isProcessRunning(L"WiFi Led Studio.exe")) {
        Sleep(100); // Đợi 100 ms trước khi kiểm tra lại
    }

    // Mở lại ambilightwifi.exe
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (!CreateProcessW(NULL, appPath, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        std::wcerr << L"Không thể khởi động lại ứng dụng. Lỗi: " << GetLastError() << std::endl;
        return 1; // Trả về 1 nếu có lỗi
    }

    // Đóng handle sau khi sử dụng
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    return 0; // Thành công
}
