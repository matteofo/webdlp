#!/usr/bin/env python3

from flask import Flask, request, Response
from yt_dlp import YoutubeDL
from contextlib import redirect_stdout
from pathlib import Path
import io, os

app = Flask(__name__)

@app.route("/")
def root():
    with open("./epic.html") as f:
        return f.read()

@app.route("/process")
def audio():
    video = request.args.get("id")
    mode = request.args.get("mode")

    ctx = {
        "outtmpl": "-",
        'logtostderr': True
    }

    if not mode:
        ctx['extract_audio'] = True
        ctx['format'] = 'bestaudio'

    buffer = io.BytesIO()
    with redirect_stdout(buffer), YoutubeDL(ctx) as yt:
        yt.download(video)

    dpath = f"{video}.mp4"
    mime = "video/mp4"

    if not mode:
        dpath = f"{video}.mp3"
        mime = "audio/mpeg"

    Path(dpath).write_bytes(buffer.getvalue())
    os.remove(dpath)
    
    return Response(buffer.getvalue(), mimetype=mime)

if __name__ == "__main__":
    app.run(debug=False, port=5106, host="0.0.0.0")