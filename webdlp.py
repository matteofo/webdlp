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

    dpath = f"{video}"

    mime = "video/mp4"
    if not mode:
        mime = "audio/mpeg"
        dpath += ".mp3"

    ctx = {
        'outtmpl': dpath,
        'logtostderr': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }

    if not mode:
        ctx['extract_audio'] = True
        ctx['format'] = 'bestaudio'

    with YoutubeDL(ctx) as yt:
        yt.download(video)

    if mode == "on":
        dpath += ".mp4"
    
    f = open(dpath, 'rb')
    contents = f.read()
    f.close()
    
    os.remove(dpath)
    
    return Response(contents, mimetype=mime)

if __name__ == "__main__":
    app.run(debug=True, port=5106, host="0.0.0.0")