"""
ShieldAI Release Packaging Script (scripts/make_release.py)

Builds a clean, production-ready distribution zip archive:
- EXCLUDES: venv, node_modules, .env, __pycache__, .git, real SQLite databases
- INCLUDES: Full backend, frontend source, chrome extension, setup scripts, doctor,
            and complete ShieldAI DistilBERT model weights and calibrated thresholds.

Usage:
    python scripts/make_release.py [--out PATH]
"""

import os
import sys
import zipfile
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {
    "venv", ".venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    ".idea", ".vscode", "dist", "build", ".system_generated"
}

EXCLUDE_FILES = {
    ".env", ".env.local", ".env.production", "shieldai.db"
}

EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".log", ".tmp"
}


def should_exclude(rel_path: str) -> bool:
    # Normalize path separators
    norm = rel_path.replace("\\", "/").strip("/")
    parts = norm.split("/")

    # Exclude directories
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True

    filename = parts[-1]
    # Exclude specific files
    if filename in EXCLUDE_FILES:
        return True
    if filename.startswith("shieldai_backup_") and filename.endswith(".db"):
        return True

    # Exclude extensions
    _, ext = os.path.splitext(filename)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return True

    return False


def make_release(output_path: str = None) -> str:
    if not output_path:
        out_dir = os.path.join(ROOT_DIR, "dist")
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "shieldai_release.zip")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    print("=" * 76)
    print(">>> [SHIELDAI] PACKAGING CLEAN DISTRIBUTION ARCHIVE")
    print("=" * 76)
    print(f"[*] Source directory: {ROOT_DIR}")
    print(f"[*] Output archive:   {output_path}")

    total_files = 0
    total_uncompressed_bytes = 0
    model_files_included = 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # In-place prune dirs to avoid traversing deep into venv or node_modules
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, ROOT_DIR)

                if should_exclude(rel_path):
                    continue

                if "models/shieldai" in rel_path.replace("\\", "/"):
                    model_files_included += 1

                file_size = os.path.getsize(abs_path)
                total_uncompressed_bytes += file_size
                total_files += 1

                zipf.write(abs_path, rel_path)

    zip_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    raw_size_mb = total_uncompressed_bytes / (1024 * 1024)

    print(f"\n[+] Archive packaged successfully:")
    print(f"    - Total Files:            {total_files}")
    print(f"    - Model Files Included:   {model_files_included}")
    print(f"    - Uncompressed Size:      {raw_size_mb:.2f} MB")
    print(f"    - Compressed Zip Size:    {zip_size_mb:.2f} MB")
    print(f"    - Archive Location:       {output_path}")
    print("=" * 76)

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package ShieldAI for release.")
    parser.add_argument("--out", type=str, default=None, help="Destination zip path")
    args = parser.parse_args()
    make_release(args.out)
