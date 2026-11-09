import sys
import os

print("Python version:", sys.version)
print("Executable:", sys.executable)

# Check VC++ Redistributable registry keys or presence
import winreg
try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64") as key:
        installed, _ = winreg.QueryValueEx(key, "Installed")
        version, _ = winreg.QueryValueEx(key, "Version")
        print(f"VC++ Redistributable X64: Installed={installed}, Version={version}")
except Exception as e:
    print("Could not query VC++ redist registry key:", e)

# Test importing torch with and without faulthandler
import faulthandler
faulthandler.enable()

try:
    import torch
    print("Torch version:", torch.__version__)
    print("Torch file:", torch.__file__)
    print("Torch CUDA available:", torch.cuda.is_available())
except Exception as e:
    print("Torch import error:", e)

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from services.model_service import ModelService
ms = ModelService.get_instance()
print("Model loaded:", ms.model_loaded)
res = ms.analyze("I will kill you")
print("Analysis score:", res["score"], "level:", res["level"])

