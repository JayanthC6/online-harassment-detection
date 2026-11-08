import os
import re

print("=== FRONTEND API CALLS ===")
for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    m = re.search(r'(apiClient|fetch)\s*\(\s*[`\'"]([^`\'"]+)[`\'"]', line)
                    if m:
                        print(f"{p}:{i+1} -> {m.group(1)}('{m.group(2)}')")

print("\n=== EXTENSION API CALLS ===")
for root, dirs, files in os.walk('extension'):
    for f in files:
        if f.endswith(('.js', '.json')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    for m in re.finditer(r'fetch\s*\(([^)]+)\)', line):
                        print(f"{p}:{i+1} -> fetch({m.group(1).strip()})")

