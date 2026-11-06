"""Web entry point for Render / local browser play."""

import os
from pathlib import Path

from flask import Flask, send_from_directory

ROOT = Path(__file__).resolve().parent

# static_url_path="" serves style.css and game.js from /, which also lets the
# same static/ folder be published as a Render Static Site without changes.
app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(ROOT / "static", "index.html")


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
