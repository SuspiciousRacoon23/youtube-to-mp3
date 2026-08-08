import yt_dlp
import concurrent.futures
import os

# Sample list of safe-to-test URLs
URLS = [
    "https://www.youtube.com/watch?v=jNQXAC9IVRw", # Me at the zoo (first youtube video)
    "https://www.youtube.com/watch?v=BaW_jenozKc", # youtube test video
]

def download_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        print(f"[{percent}] at {speed}")
    elif d['status'] == 'finished':
        print(f"[Finished] Download complete, processing {d.get('filename')}...")

def download_video(url, format_type="mp3"):
    print(f"Starting download for {url} as {format_type}...")
    
    os.makedirs('downloads', exist_ok=True)
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [download_progress_hook],
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
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
        # MP4 format
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    print("Testing concurrent YouTube downloads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_video, url, "mp3") for url in URLS]
        concurrent.futures.wait(futures)
        
    print("All downloads completed! Check the 'downloads' directory.")

if __name__ == "__main__":
    main()
