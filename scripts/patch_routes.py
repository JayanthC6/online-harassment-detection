with open('backend/api/routes_public.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the predict route header
target1 = '@public_bp.route("/predict", methods=["POST"])'
replacement1 = '@public_bp.route("/predict", methods=["POST"])\n@public_bp.route("/api/analyze", methods=["POST"])\n@public_bp.route("/analyze", methods=["POST"])'
content = content.replace(target1, replacement1, 1)

# Fix extension key check
old_check = """    if ext_api_key:
        origin = request.headers.get("Origin", "")
        # Bypass for local frontend development
        if not (origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")):
            if request.headers.get("X-Extension-Api-Key") != ext_api_key:
                return jsonify({"error": "Unauthorized: Invalid or missing X-Extension-Api-Key"}), 401"""

new_check = """    if ext_api_key:
        origin = request.headers.get("Origin", "")
        if origin and origin.startswith("chrome-extension://"):
            if request.headers.get("X-Extension-Api-Key") != ext_api_key:
                return jsonify({"error": "Unauthorized: Invalid or missing X-Extension-Api-Key"}), 401"""

content = content.replace(old_check.replace('\r\n', '\n'), new_check.replace('\r\n', '\n'))
content = content.replace(old_check, new_check)

# Add /api/batch
content = content.replace(
    '@public_bp.route("/predict/batch", methods=["POST"])',
    '@public_bp.route("/predict/batch", methods=["POST"])\n@public_bp.route("/api/batch", methods=["POST"])'
)

# Add /api/analyze/file
content = content.replace(
    '@public_bp.route("/predict/file", methods=["POST"])',
    '@public_bp.route("/predict/file", methods=["POST"])\n@public_bp.route("/api/analyze/file", methods=["POST"])\n@public_bp.route("/analyze/file", methods=["POST"])'
)

with open('backend/api/routes_public.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("routes_public.py patch completed successfully.")

