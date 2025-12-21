#!/usr/bin/env python3

from flask import *
from yt_dlp import YoutubeDL
import os, git, uuid, threading
from urllib.parse import urlparse, unquote, parse_qs

class DownloadJob():
    def __init__(self, yt, vid: str, path: str, mime: str, transcode: bool):
        self.thread = None
        self.yt = yt
        self.vid = vid
        self.path = path
        self.mime = mime
        self.transcode = transcode
        self.id = uuid.uuid4()

    def start(self):
        self.thread = threading.Thread(target=download_thread, args=[self.yt, self.vid, self.path, self.mime, self.transcode])
        self.thread.start()

app = Flask(__name__)
jobs: list[DownloadJob] = []

def download_thread(yt, video, dl_path: str, mime: str, transcode: bool):
    print(f"WORKER: {yt} {video} {dl_path}")
    yt.download(video)

    if transcode:
        print("TRANSCODING!")
        replaced = dl_path.replace(".mp4", ".tx.mp4")
        replaced = dl_path.replace(".mp3", ".tx.mp3")
        replaced = dl_path.replace(".m4a", ".tx.m4a")
        os.system(f"ffmpeg -i {dl_path} {replaced}")
    else:
        print("not transcoding.")
    
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
        path = j.path
        if j.transcode:
            path = path.replace(".mp4", ".tx.mp4")
            path = path.replace(".mp3", ".tx.mp3")
            path = path.replace(".m4a", ".tx.m4a")

        f = open(path, 'rb')
        contents = f.read()
        f.close()
        
        os.remove(j.path)
        if j.transcode:
            os.remove(path)
        
        jobs.remove(j)
        
        return Response(contents, mimetype=j.mime, content_type=j.mime, headers={
            "Content-Disposition": "attachment; filename=" + path
        })

@app.route("/process")
def process():
    video = unquote(request.args.get("id"))
    enable_video = request.args.get("video")
    transcode = request.args.get("transcode")

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

    do_transcode = None
    if not transcode or transcode == "off":
        do_transcode = False
    elif transcode == "on":
        do_transcode = True
    else:
        # invalid argument passed
        return Response("Invalid arguments", status=400)

    # set download path
    ctx['outtmpl'] = dl_path

    with YoutubeDL(ctx) as yt:
        job = DownloadJob(yt, video, dl_path, mime, do_transcode)
        jobs.append(job)
        job.start()
                
        return Response(status=307, headers={
            "Location": "./status?id=" + job.id.hex
        })

if __name__ == "__main__":
    app.run(debug=True, port=5106, host="0.0.0.0")