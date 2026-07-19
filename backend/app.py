import os

from flask import Flask, jsonify, send_from_directory

from config import REPO_ROOT
from db import SessionLocal, init_db
from routes import api_bp

FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

    init_db()
    app.register_blueprint(api_bp)

    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
