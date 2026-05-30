"""
Wasi-Tube Backend Server
========================
Requirements:
    pip install flask flask-cors yt-dlp
    sudo apt install ffmpeg   (Linux) OR  brew install ffmpeg  (Mac)

Run:
    python server.py

Then open browser:  http://localhost:5000
"""

import os
import re
import json
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)  # Allow frontend to call backend from any origin

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Store download progress per job_id
progress_store = {}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def detect_platform(url: str) -> str:
    url = url.lower()
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "instagram.com" in url:
        return "instagram"
    if "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    if "tiktok.com" in url:
        return "tiktok"
    return "unknown"


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:80]


def get_format_args(fmt: str):
    """Return yt-dlp format string and file extension."""
    fmt_map = {
        "1080p": ("bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]", "mp4"),
        "720p":  ("bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]", "mp4"),
        "480p":  ("bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]", "mp4"),
        "mp3":   ("bestaudio/best", "mp3"),
    }
    return fmt_map.get(fmt, fmt_map["720p"])


# ─────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_file("static/index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    """
    Get video metadata from URL.
    Body: { "url": "https://..." }
    Returns: title, duration, thumbnail, platform, filesize estimate
    """
    data = request.get_json()
    url = (data or {}).get("url", "").strip()

    if not url:
        return jsonify({"error": "URL khali hai!"}), 400

    platform = detect_platform(url)
    if platform == "unknown":
        return jsonify({"error": "Ye platform support nahi karta. YouTube, Instagram, Facebook, TikTok use karein."}), 400

    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            "--no-warnings",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            err = result.stderr.strip()
            return jsonify({"error": f"Video nahi mila: {err[:200]}"}), 400

        info = json.loads(result.stdout)

        return jsonify({
            "title":     info.get("title", "Unknown Title"),
            "duration":  info.get("duration_string") or fmt_seconds(info.get("duration", 0)),
            "thumbnail": info.get("thumbnail", ""),
            "uploader":  info.get("uploader") or info.get("channel", ""),
            "view_count": fmt_views(info.get("view_count", 0)),
            "platform":  platform,
            "ext":       info.get("ext", "mp4"),
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout ho gaya. Dubara try karein."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def start_download():
    """
    Start a download job.
    Body: { "url": "...", "format": "1080p"|"720p"|"480p"|"mp3" }
    Returns: { "job_id": "..." }
    """
    data = request.get_json()
    url    = (data or {}).get("url", "").strip()
    fmt    = (data or {}).get("format", "720p")

    if not url:
        return jsonify({"error": "URL khali hai!"}), 400

    job_id = os.urandom(8).hex()
    progress_store[job_id] = {"status": "queued", "percent": 0, "filename": None, "error": None}

    thread = threading.Thread(target=_download_worker, args=(job_id, url, fmt), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


def _download_worker(job_id: str, url: str, fmt: str):
    """Background thread: runs yt-dlp and updates progress."""
    format_str, ext = get_format_args(fmt)
    out_template = str(DOWNLOAD_DIR / f"%(title).60s_{job_id}.%(ext)s")

    base_cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--newline",
        "-o", out_template,
        "-f", format_str,
    ]

    if fmt == "mp3":
        base_cmd += [
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ]
    else:
        base_cmd += ["--merge-output-format", "mp4"]

    base_cmd.append(url)

    try:
        progress_store[job_id]["status"] = "downloading"
        proc = subprocess.Popen(
            base_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in proc.stdout:
            line = line.strip()
            # Parse yt-dlp progress lines like: [download]  45.3% of ...
            if "[download]" in line and "%" in line:
                m = re.search(r"(\d+\.?\d*)\s*%", line)
                if m:
                    progress_store[job_id]["percent"] = float(m.group(1))

        proc.wait()

        if proc.returncode == 0:
            # Find the downloaded file
            files = list(DOWNLOAD_DIR.glob(f"*{job_id}*"))
            if files:
                fname = files[0].name
                progress_store[job_id].update({
                    "status": "done",
                    "percent": 100,
                    "filename": fname
                })
            else:
                progress_store[job_id].update({"status": "error", "error": "File nahi mili after download."})
        else:
            progress_store[job_id].update({"status": "error", "error": "yt-dlp error. Check URL."})

    except FileNotFoundError:
        progress_store[job_id].update({
            "status": "error",
            "error": "yt-dlp install nahi hai! Pehle: pip install yt-dlp"
        })
    except Exception as e:
        progress_store[job_id].update({"status": "error", "error": str(e)})


@app.route("/api/progress/<job_id>")
def get_progress(job_id):
    """Poll download progress."""
    info = progress_store.get(job_id)
    if not info:
        return jsonify({"error": "Job nahi mila"}), 404
    return jsonify(info)


@app.route("/api/file/<filename>")
def serve_file(filename):
    """Serve the downloaded file to browser."""
    safe = sanitize_filename(Path(filename).name)
    file_path = DOWNLOAD_DIR / safe
    if not file_path.exists():
        # Also try the original filename
        file_path = DOWNLOAD_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "File nahi mili"}), 404
    return send_from_directory(DOWNLOAD_DIR, file_path.name, as_attachment=True)


# ─────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────

def fmt_seconds(secs: int) -> str:
    secs = int(secs or 0)
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fmt_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M views"
    if n >= 1_000:
        return f"{n/1_000:.0f}K views"
    return f"{n} views"


# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*45)
    print("  🔴 Wasi-Tube Server chal raha hai!")
    print("  🌐 http://localhost:5000")
    print("="*45 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
