from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
