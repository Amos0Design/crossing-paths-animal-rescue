import os
import json
import requests
from ftplib import FTP

# 1. Fetch credentials and the data payload from GitHub Actions environment
ftp_host = os.environ.get('FTP_HOST')
ftp_user = os.environ.get('FTP_USER')
ftp_pass = os.environ.get('FTP_PASSWORD')
payload_str = os.environ.get('PAYLOAD')

if not payload_str:
    print("ERROR: No payload received from Make.")
    exit(1)

payload = json.loads(payload_str)
# We expect Make to send an array of URLs under the key "photos"
photo_urls = payload.get('photos', [])

if not photo_urls:
    print("No photos found in payload. Exiting gracefully.")
    exit(0)

print(f"Successfully found {len(photo_urls)} photo entries to process.")

# 2. Connect to the FTP Server
print(f"Connecting to FTP: {ftp_host}")
ftp = FTP(ftp_host)
ftp.login(user=ftp_user, passwd=ftp_pass)

# Optional: Navigate to a specific FTP directory if needed
# ftp.cwd('/path/to/rescue/groups/folder')

# 3. Process each photo
for url in photo_urls:
    # SAFETY CHECK: Skip if the URL is blank or just spaces
    if not url or not url.strip():
        print("Skipping empty URL entry.")
        continue

    print(f"\nDownloading: {url}")
    
    # Strip the URL to get just the filename (e.g., "dog123.jpg")
    filename = url.split('/')[-1]
    
    # If the URL has query parameters at the end (like ?v=123), remove them
    if '?' in filename:
        filename = filename.split('?')[0]

    # Download the image from the shelter software
    response = requests.get(url)
    if response.status_code == 200:
        # Save it temporarily to the GitHub Action runner
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        # Upload it directly to the FTP
        print(f"Uploading {filename} to FTP...")
        with open(filename, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        # Delete the temporary file to keep the workspace clean
        os.remove(filename)
        print(f"Success: {filename}")
    else:
        print(f"FAILED: Could not download {url}. Status Code: {response.status_code}")

# Close the FTP connection
ftp.quit()
print("\nAll photos processed.")
