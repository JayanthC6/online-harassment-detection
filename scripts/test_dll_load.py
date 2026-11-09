import glob
import os
import ctypes
import faulthandler

faulthandler.enable()

th_dll_path = os.path.join(os.path.dirname(ctypes.__file__), "..", "site-packages", "torch", "lib")
th_dll_path = os.path.abspath("venv/Lib/site-packages/torch/lib")
print("DLL Path:", th_dll_path)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dlls = glob.glob(os.path.join(th_dll_path, "*.dll"))
for dll in dlls:
    print("Testing LoadLibraryExW:", os.path.basename(dll))
    try:
        res = kernel32.LoadLibraryExW(dll, None, 0x00001100)
        err = ctypes.get_last_error()
        print(f"  Result: {res}, LastError: {err}")
    except Exception as e:
        print(f"  Exception: {e}")

