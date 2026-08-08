import yt_dlp
import os
import requests
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

API_URL = "http://localhost:8000/api/internal/progress"

class MyLogger(object):
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def create_hook(batch_id, url):
    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '0B/s').strip()
            # In a real app we might debounce this so we don't spam HTTP
            try:
                requests.post(API_URL, json={
                    "batch_id": batch_id,
                    "url": url,
                    "status": "downloading",
                    "percent": percent,
                    "speed": speed
                })
            except:
                pass
        elif d['status'] == 'finished':
            try:
                requests.post(API_URL, json={
                    "batch_id": batch_id,
                    "url": url,
                    "status": "finished",
                    "filename": d.get('filename')
                })
            except:
                pass
    return hook

@app.task
def process_batch(batch_id, urls, format_type):
    os.makedirs(f'downloads/{batch_id}', exist_ok=True)
    
    for url in urls:
        ydl_opts = {
            'outtmpl': f'downloads/{batch_id}/%(title)s.%(ext)s',
            'progress_hooks': [create_hook(batch_id, url)],
            'quiet': True,
            'nocheckcertificate': True,
            'logger': MyLogger(),
        }
        
        if format_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            try:
                requests.post(API_URL, json={
                    "batch_id": batch_id,
                    "url": url,
                    "status": "error",
                    "error_msg": str(e)
                })
            except:
                pass
