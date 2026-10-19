import os
import json
import requests
from ftplib import FTP
import yt_dlp

# 1. Fetch credentials and the data payload
ftp_host = os.environ.get('FTP_HOST')
ftp_user = os.environ.get('FTP_USER')
ftp_pass = os.environ.get('FTP_PASSWORD')
payload_str = os.environ.get('PAYLOAD')

if not payload_str:
    print("ERROR: No payload received from Make.")
    exit(1)

payload = json.loads(payload_str)
raw_photos = payload.get('photos', [])
raw_videos = payload.get('videos', []) # Add this to your Make JSON payload

# 2. UNPACKING: Fix Make's formatting quirks
def extract_urls(raw_list):
    urls = []
    for item in raw_list:
        if isinstance(item, str):
            split_links = item.split(',')
            for link in split_links:
                clean_link = link.strip()
                if clean_link:
                    urls.append(clean_link)
        else:
            urls.append(item)
    return urls

photo_urls = extract_urls(raw_photos)
video_urls = extract_urls(raw_videos)

print(f"Found {len(photo_urls)} photos and {len(video_urls)} videos to process.")

# 3. Connect to the FTP Server
print(f"Connecting to FTP: {ftp_host}")
ftp = FTP(ftp_host)
ftp.login(user=ftp_user, passwd=ftp_pass)

# 4. Process Photos
if photo_urls:
    ftp.cwd('/import/pictures')
    print("Navigated to folder: /import/pictures")
    
    for url in photo_urls:
        print(f"\nDownloading Photo: {url}")
        filename = url.split('/')[-1].split('?')[0]
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"Uploading {filename} to FTP...")
            with open(filename, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            os.remove(filename)
            print(f"Success: {filename}")
        else:
            print(f"FAILED: Could not download {url}. Status Code: {response.status_code}")

# 5. Process YouTube Videos
if video_urls:
    ftp.cwd('/') # Reset to root before navigating
    ftp.cwd('/import/videos') # Adjust to your actual video folder path
    print("\nNavigated to folder: /import/videos")
    
    for url in video_urls:
        print(f"\nDownloading Video: {url}")
        temp_filename = 'temp_video.mp4'
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': temp_filename,
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info to get the actual video title for the final filename
                info_dict = ydl.extract_info(url, download=True)
                video_title = ydl.prepare_filename(info_dict)
                # Ensure it has an mp4 extension for the FTP
                final_filename = video_title.split('.')[0] + '.mp4' 
                # sanitize filename for FTP (remove spaces/special characters)
                final_filename = "".join([c for c in final_filename if c.isalpha() or c.isdigit() or c==' ']).rstrip() + ".mp4"
                final_filename = final_filename.replace(" ", "_")

            print(f"Uploading {final_filename} to FTP...")
            with open(temp_filename, 'rb') as f:
                ftp.storbinary(f'STOR {final_filename}', f)
            
            os.remove(temp_filename)
            print(f"Success: {final_filename}")
            
        except Exception as e:
            print(f"FAILED: Could not process video {url}. Error: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

# Close the FTP connection
ftp.quit()
print("\nAll tasks processed.")
