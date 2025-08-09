# webdlp
a simple web interface/api to download videos with yt-dlp

# api
### /: web interface
shows a simple web interface (no js) to download a file.

### /process: download files
`[server:port]/process?id=[video id]&video[on|off]`

downloads a file; omitting the `video` parameter or setting it to `off` will download the audio track only.