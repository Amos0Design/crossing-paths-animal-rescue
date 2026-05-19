import os
import json
import requests
# from ftplib import FTP  <-- Commented out for testing

payload_str = os.environ.get('PAYLOAD')

print("--- TEST MODE INITIATED ---")
print(f"Raw Payload received from Make: {payload_str}")

if not payload_str:
    print("ERROR: No payload received from Make.")
    exit(1)

payload = json.loads(payload_str)
photo_urls = payload.get('photos', [])

if not photo_urls:
    print("ERROR: No photos array found in payload.")
    exit(0)

print(f"Successfully found {len(photo_urls)} photos to process.")

# Process each photo
for url in photo_urls:
    # SAFETY CHECK: Skip if the URL is blank or just spaces
    if not url or not url.strip():
        print("Skipping empty URL entry.")
        continue

    print(f"\nAttempting to download: {url}")
    filename = url.split('/')[-1]
    if '?' in filename:
        filename = filename.split('?')[0]

    response = requests.get(url)
    if response.status_code == 200:
        print(f"SUCCESS: Downloaded {filename}.")
        print(f"PRETENDING TO UPLOAD: {filename} to FTP...")
        # FTP upload code is safely removed for this test
    else:
        print(f"FAILED: Could not download {url}. Status: {response.status_code}")
        
print("\n--- TEST COMPLETE ---")
