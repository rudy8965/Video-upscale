from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import subprocess, os, uuid, tempfile
from pathlib import Path

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

UPLOAD = Path(tempfile.gettempdir()) / "upscale"
UPLOAD.mkdir(exist_ok=True)

RESOLUTIONS = {
    "4k": (2160, 3840),
    "2k": (1440, 2560),
    "1080p": (1080, 1920),
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upscale", methods=["POST"])
def upscale():
    if "video" not in request.files:
        return jsonify({"error": "Tidak ada video"}), 400

    f = request.files["video"]
    if not f.filename:
        return jsonify({"error": "File kosong"}), 400

    res = request.form.get("res", "4k")
    w, h = RESOLUTIONS.get(res, (2160, 3840))

    job = str(uuid.uuid4())[:8]
    inp = UPLOAD / f"{job}_in.mp4"
    out = UPLOAD / f"{job}_out.mp4"

    try:
        f.save(inp)

        cmd = [
            "ffmpeg", "-y", "-i", str(inp),
            "-vf", f"scale={w}:{h}:flags=lanczos",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=180)

        if result.returncode != 0 or not out.exists():
            return jsonify({"error": "Gagal proses video"}), 500

        return send_file(out, as_attachment=True, download_name="upscaled.mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        inp.unlink(missing_ok=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
