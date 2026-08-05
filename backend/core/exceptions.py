from flask import jsonify

class AppException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"error": self.message}

def register_error_handlers(app):
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        return jsonify(e.to_dict()), e.status_code

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Internal Server Error"}), 500
