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

### Option A — Blueprint (recommended)

1. Push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), choose **New → Blueprint**.
3. Select this repository. Render reads `render.yaml` and creates the free Python web service.
4. When the build finishes, open the service's `onrender.com` URL.

### Option B — Existing Web Service

If the service already exists, open **Settings** and use:

| Setting | Value |
| --- | --- |
| **Language / Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60` |
| **Health Check Path** | `/health` |

Add an environment variable `PYTHON_VERSION=3.12.7` on the **Environment** page.

> **Important:** create a **Web Service**, not a **Static Site**. A Static Site has no Python
> runtime, so `pip install` fails with `pip: command not found`.

`requirements.txt` is web-only (Flask + Gunicorn) so Render does not try to build pygame. Use
`requirements-desktop.txt` for the local pygame game.

### Option C — Static Site (fallback)

The browser game is plain HTML/CSS/JS, so it can also be hosted without Python:

| Setting | Value |
| --- | --- |
| **Type** | Static Site |
| **Build Command** | *(leave empty)* |
| **Publish Directory** | `static` |

Asset paths in `static/index.html` are relative, so this works out of the box.

## Troubleshooting

- **`Port scan timeout reached` / `No open ports detected`** — the server must listen on
  `0.0.0.0` and on the port Render provides in `$PORT`. The start command above does both.
- **`ModuleNotFoundError: No module named 'flask'`** — the build command is missing or
  `requirements.txt` was not installed. Use `pip install -r requirements.txt`.
- **`gunicorn: command not found`** — `gunicorn` must be listed in `requirements.txt` (it is).
- **`pip: command not found`** — the service was created with the wrong runtime. Recreate it as
  **Python 3** (or use the Static Site fallback above).
- **Python version** — Render no longer reads `runtime.txt`. Set `PYTHON_VERSION` or add a
  `.python-version` file (both are already set to `3.12.7` here).
- **First request is slow** — free services spin down after inactivity and take up to a minute
  to wake up. This is expected.
