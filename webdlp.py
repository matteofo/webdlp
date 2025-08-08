#!/usr/bin/env python3

from flask import *
from yt_dlp import YoutubeDL
from contextlib import redirect_stdout
from pathlib import Path
import io, os, git

app = Flask(__name__)

def get_commit() -> str:
    repo = git.Repo("./")
    return repo.head.object.hexsha[:7]

@app.route("/")
def root():
    return render_template("index.html", commit=get_commit())

@app.route("/process")
def audio():
    video = request.args.get("id")
    mode = request.args.get("mode")

    dpath = f"{video}"

    # check selected mode (video/audio)
    mime = "video/mp4"
    if not mode:
        mime = "audio/mp4"
        dpath += ".m4a"

    # set yt-dlp opts
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
    
    # read file to ram
    f = open(dpath, 'rb')
    contents = f.read()
    f.close()
    
    # delete from fs
    os.remove(dpath)
    
    headers = {
        "Content-Disposition": "attachment; filename=" + dpath
    }
    return Response(contents, mimetype=mime, content_type=mime, headers=headers)

if __name__ == "__main__":
    app.run(debug=True, port=5106, host="0.0.0.0")