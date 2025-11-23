import requests
import cv2
import numpy as np
import time
import sys

def test_app():
    print("Testing API connectivity...")
    try:
        r = requests.get("http://localhost:8000/template")
        if r.status_code != 200:
            print(f"Failed to get template: {r.status_code}")
            return False
        print("API is up.")
    except Exception as e:
        print(f"API connection failed: {e}")
        return False

    print("Generating test image...")
    # Create 7x9 grid
    # 7 rows, 9 cols
    h, w = 700, 900
    img = np.ones((h, w), dtype=np.uint8) * 255 # White background
    
    # Draw grid lines (optional, but let's just draw a letter)
    # First cell: row 0, col 0.
    # x: 0-100, y: 0-100
    # Draw 'A'
    cv2.putText(img, "A", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0,), 5)
    
    # Encode
    _, buf = cv2.imencode(".png", img)
    
    print("Uploading image...")
    files = {"sample": ("test.png", buf.tobytes(), "image/png")}
    try:
        r = requests.post("http://localhost:8000/upload", files=files)
        if r.status_code != 200:
            print(f"Upload failed: {r.text}")
            return False
        data = r.json()
        job_id = data["job_id"]
        print(f"Job ID: {job_id}")
    except Exception as e:
        print(f"Upload request failed: {e}")
        return False
        
    # Poll for status (since we can't easily do websocket in this script without extra libs)
    # Wait a bit and check redis directly via docker exec?
    # Or just wait and check if file exists in container?
    # The API doesn't have a polling endpoint, only websocket.
    # But I can check if the file is downloadable.
    
    print("Waiting for processing...")
    time.sleep(5)
    
    font_url = f"http://localhost:8000/download/{job_id}.ttf"
    print(f"Checking {font_url}...")
    
    for i in range(10):
        r = requests.head(font_url)
        if r.status_code == 200:
            print("Font generated successfully!")
            return True
        print("Waiting...")
        time.sleep(2)
        
    print("Timeout waiting for font.")
    return False

if __name__ == "__main__":
    if test_app():
        sys.exit(0)
    else:
        sys.exit(1)
