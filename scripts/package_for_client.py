#!/usr/bin/env python3
"""
ShieldAI Client Release Packager
Creates a clean, production-ready ZIP archive ready to share with clients or examiners.
Excludes heavy build artifacts, virtual environments, node_modules, and git history.
"""

import os
import sys
import zipfile
from pathlib import Path

# Directories to exclude from the release ZIP
EXCLUDE_DIRS = {
    'venv',
    '.venv',
    'node_modules',
    '.git',
    '__pycache__',
    '.pytest_cache',
    '.vite',
    'dist'
}

# File extensions to exclude
EXCLUDE_EXTENSIONS = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.log',
    '.sqlite-journal',
    '.zip'
}

# Specific files to exclude
EXCLUDE_EXACT_FILES = {
    '.DS_Store',
    'Thumbs.db',
    'ShieldAI_Client_Release.zip'
}

def create_client_zip(output_zip_path=None):
    root_dir = Path(__file__).resolve().parent.parent
    if output_zip_path is None:
        output_zip_path = root_dir / "ShieldAI_Client_Release.zip"
    else:
        output_zip_path = Path(output_zip_path)

    print("=" * 65)
    print("   ShieldAI - Packaging Clean Project Archive for Client")
    print("=" * 65)
    print(f"[*] Project Root : {root_dir}")
    print(f"[*] Target ZIP   : {output_zip_path}")
    print("[*] Filtering out 'venv', 'node_modules', '.git', and cache files...")

    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for current_path, dirs, files in os.walk(root_dir):
            rel_dir = os.path.relpath(current_path, root_dir)
            parts = Path(rel_dir).parts

            # Skip excluded directories
            if any(part in EXCLUDE_DIRS for part in parts):
                continue

            for file in files:
                file_path = Path(current_path) / file
                rel_file = os.path.relpath(file_path, root_dir)
                file_parts = Path(rel_file).parts

                if any(part in EXCLUDE_DIRS for part in file_parts):
                    continue

                if file_path.suffix in EXCLUDE_EXTENSIONS:
                    continue

                if file in EXCLUDE_EXACT_FILES:
                    continue

                # Add file to zip archive under top-level 'online-harassment-detection/' folder
                arcname = os.path.join("online-harassment-detection", rel_file)
                zipf.write(file_path, arcname)
                file_count += 1
                total_uncompressed_bytes += file_path.stat().st_size

    zip_size_mb = output_zip_path.stat().st_size / (1024 * 1024)
    raw_size_mb = total_uncompressed_bytes / (1024 * 1024)

    print(f"\n[+] Success! Created: {output_zip_path}")
    print(f"    - Included files: {file_count:,}")
    print(f"    - Uncompressed  : {raw_size_mb:.2f} MB")
    print(f"    - Compressed ZIP: {zip_size_mb:.2f} MB")
    print("=" * 65)
    return output_zip_path

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    create_client_zip(out_path)
