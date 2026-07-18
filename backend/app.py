from flask import Flask, jsonify

from db import SessionLocal, init_db
from routes import api_bp


def create_app():
    app = Flask(__name__)

    init_db()
    app.register_blueprint(api_bp)

    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
