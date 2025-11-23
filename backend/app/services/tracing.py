import cv2
import numpy as np
import subprocess
import os
import uuid
import xml.etree.ElementTree as ET

def extract_glyphs(img_bytes: bytes) -> dict:
    # Decode image
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Could not decode image")

    # Threshold (Inverted: Text is white, background black)
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Grid logic
    h, w = img.shape
    rows = 7
    cols = 9
    cell_w = w // cols
    cell_h = h // rows
    
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    results = {}
    
    for i, char in enumerate(chars):
        r = i // cols
        c = i % cols
        
        x = c * cell_w
        y = r * cell_h
        
        # Extract cell
        pad_x = int(cell_w * 0.1)
        pad_y = int(cell_h * 0.1)
        
        roi = binary[y+pad_y : y+cell_h-pad_y, x+pad_x : x+cell_w-pad_x]
        
        # Check if empty
        if cv2.countNonZero(roi) == 0:
            continue
            
        # Potrace needs black text on white background
        # We have white text on black background (roi)
        # So invert it
        roi_inv = cv2.bitwise_not(roi)
        
        tmp_id = str(uuid.uuid4())
        bmp_path = f"/tmp/{tmp_id}.bmp"
        svg_path = f"/tmp/{tmp_id}.svg"
        
        try:
            cv2.imwrite(bmp_path, roi_inv)
            
            # Run potrace
            # -s: SVG
            # --flat: simpler paths
            subprocess.run(["potrace", "-s", "--flat", "-o", svg_path, bmp_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(svg_path):
                tree = ET.parse(svg_path)
                root = tree.getroot()
                # Namespace handling
                # SVG usually has a namespace
                ns = {'svg': 'http://www.w3.org/2000/svg'}
                
                paths = []
                # Find all paths
                for path in root.findall(".//{http://www.w3.org/2000/svg}path"):
                    d = path.get('d')
                    if d:
                        paths.append(d)
                
                if paths:
                    results[char] = " ".join(paths)
                    
        except Exception as e:
            print(f"Error tracing {char}: {e}")
        finally:
            if os.path.exists(bmp_path): os.remove(bmp_path)
            if os.path.exists(svg_path): os.remove(svg_path)
        
    return results
