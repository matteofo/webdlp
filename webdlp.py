#!/usr/bin/env python3

from flask import *
from yt_dlp import YoutubeDL
import os, git

app = Flask(__name__)

def get_commit() -> str:
    repo = git.Repo("./")
    return repo.head.object.hexsha[:7]

@app.route("/")
def root():
    return render_template("index.html", commit=get_commit())

@app.route("/process")
def process():
    video = request.args.get("id")
    enable_video = request.args.get("video")

    # video id must be passed
    if not video:
        return Response("Invalid arguments", status=400)

    dl_path = f"{video}"

    # yt-dlp opts
    ctx = {
        'logtostderr': True,
    }

    # check selected if video is enbled
    if not enable_video or enable_video == "off":
        # set yt-dlp to download only the audio track
        # audio still seems to be encoded as mp4 (m4a) most of the time
        mime = "audio/mp4"
        dl_path += ".m4a"

        ctx['extract_audio'] = True
        ctx['format'] = 'bestaudio'
    elif enable_video == "on":
        # set yt-dlp to download the best video format available
        mime = "video/mp4"
        dl_path += ".mp4"
        
        ctx['format'] = 'bestvideo+bestaudio/best[ext=mp4]/best'
    else:
        # invalid argument passed
        return Response("Invalid arguments", status=400)
    
    # set download path
    ctx['outtmpl'] = dl_path

    with YoutubeDL(ctx) as yt:
        yt.download(video)
    
        # read file to ram
        f = open(dl_path, 'rb')
        contents = f.read()
        f.close()
        
        # delete from fs
        os.remove(dl_path)
        
        # tell browser this is an attachment
        headers = {
            "Content-Disposition": "attachment; filename=" + dl_path
        }

        return Response(contents, mimetype=mime, content_type=mime, headers=headers)

if __name__ == "__main__":
    app.run(debug=True, port=5106, host="0.0.0.0")