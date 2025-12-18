#!/usr/bin/env python3

from flask import *
from yt_dlp import YoutubeDL
import os, git, uuid, threading
from urllib.parse import urlparse, unquote, parse_qs

class DownloadJob():
    def __init__(self, thread: threading.Thread, vid: str, path: str, mime: str):
        self.thread = thread
        self.vid = vid
        self.path = path
        self.mime = mime
        self.id = uuid.uuid4()

app = Flask(__name__)
jobs: list[DownloadJob] = []

def download_thread(yt, video, dl_path):
    print(f"WORKER: {yt} {video} {dl_path}")
    yt.download(video)
    
def get_commit() -> str:
    repo = git.Repo("./")
    return repo.head.object.hexsha[:7]

def get_commit_msg() -> str:
    repo = git.Repo("./")
    return repo.head.object.message

def self_update():
    repo = git.Repo("./")
    repo.remotes.origin.pull()

@app.route("/")
def root():
    self_update()
    return render_template("index.html", commit=get_commit(), commit_msg=get_commit_msg())
    
@app.route("/status")
def status():
    id = request.args.get("id")
    if not id:
        return Response("Invalid arguments", status=400)
    
    job = None
    
    for j in jobs:
        if j.id.hex == id:
            job = j
            
    if job is None:
        return Response("No such job!", 404)
            
    if job.thread.is_alive():
        resp = make_response(render_template("status.html", video_id=j.vid))
        resp.headers.set("Refresh", "1")
        return resp
    else:
        # read file to ram
        f = open(j.path, 'rb')
        contents = f.read()
        f.close()
        
        os.remove(j.path)
        
        jobs.remove(j)
        
        return Response(contents, mimetype=j.mime, content_type=j.mime, headers={
            "Content-Disposition": "attachment; filename=" + j.path
        })

@app.route("/process")
def process():
    video = unquote(request.args.get("id"))
    enable_video = request.args.get("video")

    # video id must be passed
    if not video:
        return Response("Invalid arguments", status=400)
    
    # check if input is url or just an id
    if video.startswith("http"):
        video_url = urlparse(video)
        query = parse_qs(video_url.query)

        if "v" not in query:
            return Response("Invalid arguments", status=400)
        else:
            video = query["v"][0]

    dl_path = f"{video}"

    # yt-dlp opts
    ctx = {
        'logtostderr': True
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
        
        ctx['format'] = 'bestvideo+bestaudio'
    else:
        # invalid argument passed
        return Response("Invalid arguments", status=400)
    
    # set download path
    ctx['outtmpl'] = dl_path

    with YoutubeDL(ctx) as yt:      
        dl_thread = threading.Thread(target=download_thread, args=[yt, video, dl_path])
        job = DownloadJob(dl_thread, video, dl_path, mime)
        jobs.append(job)
        
        dl_thread.start()
        
        return Response(status=308, headers={
            "Location": "./status?id=" + job.id.hex
        })

if __name__ == "__main__":
    app.run(debug=True, port=5106, host="0.0.0.0")