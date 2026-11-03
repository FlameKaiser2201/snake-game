# Smooth Snake

A classic Snake game with interpolated movement so the snake glides instead of jumping cell-to-cell.

There are two ways to play:

- **Desktop (pygame):** `python game.py`
- **Browser (Render / Flask):** open the web app and play in the canvas

The web version exists because pygame needs a local window. Render hosts the browser game.

## Local desktop game

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-desktop.txt
python game.py
```

Controls: **Arrows / WASD**, **Space** pause, **R** restart, **Esc** quit.

## Local web game

```bash
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Deploy on Render

1. Push this repository to GitHub.
2. In [Render](https://dashboard.render.com), create a **New Web Service** from the repo.
3. Render can use `render.yaml`, or set:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Deploy. The public URL serves the browser Snake game.

`requirements.txt` is web-only (Flask + Gunicorn) so Render does not try to build pygame. Use `requirements-desktop.txt` for the local pygame game.
