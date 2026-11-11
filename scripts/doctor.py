"""
ShieldAI Diagnostic & System Doctor Utility (scripts/doctor.py)

Performs comprehensive diagnostic checks:
1. Python & Node.js versions
2. PyTorch import and C++ DLL runtime verification
3. ShieldAI DistilBERT model files & calibrated thresholds
4. Optional tools (RapidOCR, Tesseract, Whisper, Anthropic API)
5. Port availability (5000 Backend, 5173 Frontend)
6. .env configuration and secret settings

Usage:
    python scripts/doctor.py
"""

import sys
import os
import socket
import subprocess
import json

# Ensure project root and backend are in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def check_port(port: int, host: str = "127.0.0.1") -> bool:
    """Returns True if the port is currently available to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False


def run():
    print("=" * 76)
    print(">>> [SHIELDAI] SYSTEM HEALTH & ENVIRONMENT DOCTOR")
    print("=" * 76)

    all_passed = True
    warnings = []

    # ── 1. Python Environment ──
    py_ver = sys.version_info
    py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    root_venv = os.path.join(ROOT_DIR, "venv")
    is_root_venv = False
    try:
        if os.path.exists(root_venv):
            is_root_venv = os.path.samefile(sys.prefix, root_venv)
    except Exception:
        pass

    if is_root_venv:
        print(f"  [OK]   Virtual Environment:   Root venv ({os.path.relpath(root_venv, ROOT_DIR)})")
    else:
        print(f"  [INFO] Virtual Environment:   {sys.prefix}")

    if py_ver >= (3, 10):
        print(f"  [OK]   Python Version:        {py_str} (>= 3.10 required)")
    else:
        print(f"  [FAIL] Python Version:        {py_str} (Python >= 3.10 required)")
        all_passed = False

    # ── 2. Node.js Environment ──
    try:
        node_res = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=5)
        if node_res.returncode == 0:
            node_ver = node_res.stdout.strip()
            print(f"  [OK]   Node.js Version:       {node_ver}")
        else:
            print(f"  [WARN] Node.js Version:       Not found or non-zero exit")
            warnings.append("Node.js not detected on PATH; required for frontend dev server.")
    except Exception:
        print(f"  [WARN] Node.js Version:       Not found on system PATH")
        warnings.append("Node.js not installed or not on PATH.")

    # ── 3. PyTorch & C++ Runtime ──
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        device_str = f"CUDA ({torch.cuda.get_device_name(0)})" if cuda_avail else "CPU"
        print(f"  [OK]   PyTorch Runtime:       v{torch.__version__} ({device_str})")
    except Exception as e:
        print(f"  [WARN] PyTorch Runtime:       Failed to load ({e})")
        warnings.append("PyTorch failed to initialize. System will operate in rules-only fallback mode.")

    # ── 4. ShieldAI Model Files ──
    model_dir = os.path.join(BACKEND_DIR, "models", "shieldai")
    required_model_files = ["model.safetensors", "config.json", "thresholds.json"]
    missing_files = []
    if os.path.exists(model_dir):
        for rf in required_model_files:
            if not os.path.exists(os.path.join(model_dir, rf)):
                missing_files.append(rf)

        if not missing_files:
            try:
                with open(os.path.join(model_dir, "thresholds.json"), "r") as f:
                    th = json.load(f)
                print(f"  [OK]   Model Files:           Present in {os.path.relpath(model_dir, ROOT_DIR)} ({len(th)} calibrated thresholds)")
            except Exception:
                print(f"  [OK]   Model Files:           Present in {os.path.relpath(model_dir, ROOT_DIR)}")
        else:
            print(f"  [WARN] Model Files:           Missing: {missing_files} -> rules-only mode active")
            warnings.append(f"Model directory missing files: {missing_files}. Running rules-only.")
    else:
        print(f"  [WARN] Model Files:           Directory missing ({model_dir}) -> rules-only mode active")
        warnings.append("Model directory not found. Running rules-only fallback mode.")

    # ── 5. Optional Tools & Modules ──
    # RapidOCR
    try:
        from rapidocr_onnxruntime import RapidOCR
        print("  [OK]   OCR Primary Engine:    rapidocr-onnxruntime (Offline ONNX)")
    except Exception:
        # Check Tesseract fallback
        import shutil
        tess = shutil.which("tesseract")
        if tess:
            print(f"  [OK]   OCR Fallback Engine:   Tesseract ({tess})")
        else:
            print("  [WARN] OCR Engine:            rapidocr-onnxruntime and Tesseract not detected")
            warnings.append("No OCR engine available for screenshot analysis.")

    # Audio transcription (Whisper)
    try:
        import faster_whisper
        print("  [OK]   Audio Engine:          faster-whisper")
    except Exception:
        print("  [INFO] Audio Engine:          faster-whisper not installed (optional)")

    # Anthropic Claude API Key
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key and not anthropic_key.startswith("your_"):
        print("  [OK]   LLM Chatbot API:       ANTHROPIC_API_KEY configured")
    else:
        print("  [INFO] LLM Chatbot API:       ANTHROPIC_API_KEY not set (Rule-based fallback active)")

    # ── 6. Port Availability ──
    p5000_ok = check_port(5000)
    p5173_ok = check_port(5173)

    if p5000_ok:
        print("  [OK]   Backend Port 5000:     Available")
    else:
        print("  [INFO] Backend Port 5000:     In use (backend server may already be running)")

    if p5173_ok:
        print("  [OK]   Frontend Port 5173:    Available")
    else:
        print("  [INFO] Frontend Port 5173:    In use (Vite dev server may already be running)")

    # ── 7. Environment & Config (.env) ──
    env_file = os.path.join(ROOT_DIR, ".env")
    backend_env = os.path.join(BACKEND_DIR, ".env")
    if os.path.exists(env_file) or os.path.exists(backend_env):
        print("  [OK]   Environment File:      .env found")
    else:
        print("  [INFO] Environment File:      .env not found (using default dev configuration)")

    print("=" * 76)
    if all_passed and not warnings:
        print(">>> [SUCCESS] All core and optional ShieldAI components verified operational!")
    elif all_passed:
        print(f">>> [OPERATIONAL] Core system verified with {len(warnings)} non-critical notices:")
        for w in warnings:
            print(f"    - {w}")
    else:
        print(">>> [FAILED] Core dependencies missing. Please address the errors above.")
    print("=" * 76)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run())

