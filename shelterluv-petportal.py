import os
import json
import requests
from ftplib import FTP

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

# 2. UNPACKING: Fix Make's formatting quirks
photo_urls = []
for item in raw_photos:
    if isinstance(item, str):
        # If Make sent one giant comma-separated string, split it into separate links
        split_links = item.split(',')
        for link in split_links:
            clean_link = link.strip() # Remove any extra spaces
            if clean_link:
                photo_urls.append(clean_link)
    else:
        photo_urls.append(item)

if not photo_urls:
    print("No photos found in payload. Exiting gracefully.")
    exit(0)

# This should now accurately print "Successfully found 4 photo entries..."
print(f"Successfully found {len(photo_urls)} photo entries to process.")

# 3. Connect to the FTP Server
print(f"Connecting to FTP: {ftp_host}")
ftp = FTP(ftp_host)
ftp.login(user=ftp_user, passwd=ftp_pass)

# 4. Process each photo
for url in photo_urls:
    print(f"\nDownloading: {url}")
    
    # Strip the URL to get just the filename
    filename = url.split('/')[-1]
    
    # Clean up the filename if there are query parameters
    if '?' in filename:
        filename = filename.split('?')[0]

    # Download disguised as a standard web browser
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Save it temporarily
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        # Upload it to FTP
        print(f"Uploading {filename} to FTP...")
        with open(filename, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        # Delete temporary file
        os.remove(filename)
        print(f"Success: {filename}")
    else:
        print(f"FAILED: Could not download {url}. Status Code: {response.status_code}")

# Close the FTP connection
ftp.quit()
print("\nAll photos processed.")
