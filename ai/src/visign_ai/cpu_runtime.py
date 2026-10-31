"""Configure only the current inference process, without changing the machine power plan.

Windows policy reference:
https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation
"""

import os
import sys


def configure_cpu_runtime():
    requested = os.environ.get("VISIGN_CPU_PERFORMANCE_MODE", "1")
    if requested not in ("0", "1"):
        raise ValueError("VISIGN_CPU_PERFORMANCE_MODE must be 0 or 1")
    if requested == "0" or sys.platform != "win32":
        return {"mode": "system-default", "applied": False}
    try:
        _set_windows_performance_mode()
    except (AttributeError, OSError) as error:
        return {
            "mode": "windows-high-qos",
            "applied": False,
            "error": type(error).__name__,
        }
    return {"mode": "windows-high-qos", "applied": True}


def _set_windows_performance_mode():
    import ctypes
    from ctypes import wintypes

    class PowerState(ctypes.Structure):
        _fields_ = [
            ("Version", wintypes.ULONG),
            ("ControlMask", wintypes.ULONG),
            ("StateMask", wintypes.ULONG),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    signature = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.GetProcessInformation.argtypes = signature
    kernel.SetProcessInformation.argtypes = signature
    handle = kernel.GetCurrentProcess()
    state = PowerState(1, 0, 0)
    if not kernel.GetProcessInformation(
        handle, 4, ctypes.byref(state), ctypes.sizeof(state)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    # Take control of execution-speed throttling and turn it off. Preserve other bits.
    state.ControlMask |= 1
    state.StateMask &= ~1
    if not kernel.SetProcessInformation(
        handle, 4, ctypes.byref(state), ctypes.sizeof(state)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
