import os
import signal
import sys

SHELLS = {"cmd.exe", "powershell.exe", "pwsh.exe"}
LAUNCHERS = {"python.exe", "pythonw.exe", "py.exe", "larp.exe"}


def _processes():
    """Map pid -> (parent pid, exe name) using the Windows process snapshot."""
    import ctypes
    from ctypes import wintypes

    class ENTRY(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    k = ctypes.windll.kernel32
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k.CreateToolhelp32Snapshot(0x2, 0)
    procs, e = {}, ENTRY()
    e.dwSize = ctypes.sizeof(ENTRY)
    ok = k.Process32FirstW(snap, ctypes.byref(e))
    while ok:
        procs[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile.lower())
        ok = k.Process32NextW(snap, ctypes.byref(e))
    k.CloseHandle(snap)
    return procs


def find_shells():
    """Shell processes that (directly or through launchers) started this program."""
    procs, found, pid = _processes(), [], os.getpid()
    while pid in procs:
        ppid, _ = procs[pid]
        if ppid not in procs:
            break
        name = procs[ppid][1]
        if name in SHELLS:
            found.append(ppid)
        elif name not in LAUNCHERS:
            break
        pid = ppid
    return found


def close_terminal():
    """End the shell that is hosting LARP so its terminal window or tab closes."""
    if not sys.stdout.isatty():
        return
    try:
        if os.name == "nt":
            import ctypes

            k = ctypes.windll.kernel32
            for pid in find_shells():
                handle = k.OpenProcess(0x0001, False, pid)
                if handle:
                    k.TerminateProcess(handle, 0)
                    k.CloseHandle(handle)
        else:
            os.kill(os.getppid(), signal.SIGHUP)
    except Exception:
        pass
