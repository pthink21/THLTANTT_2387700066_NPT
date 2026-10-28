"""Minimal Flask service used to demonstrate security checks in CI."""

import os
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY")

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/")
    def index():
        return jsonify(
            application="devsecops-demo",
            student="Nguyễn Phúc Thịnh",
            student_id="2387700066",
            message="Security checks run before deployment.",
        )

    return app


app = create_app()
