from flask import Flask, jsonify

from db import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
