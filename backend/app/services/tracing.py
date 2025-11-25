import cv2
import numpy as np
import subprocess
import os
import uuid
import xml.etree.ElementTree as ET

def roughen_glyph(img: np.ndarray) -> np.ndarray:
    """
    Apply noise and morphological operations to simulate 
    rough edges and ink bleed of realistic penmanship.
    Input: Grayscale image (0=black ink, 255=white paper)
    """
    h, w = img.shape
    
    # 1. Add Gaussian noise to break up perfect edges
    # Standard deviation 10 seems to provide good texture without destroying shape
    noise = np.random.normal(0, 10, (h, w)).astype(np.int16)
    
    noisy_img = img.astype(np.int16) + noise
    noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
    
    # 2. Gaussian Blur to soften the noise into organic curves
    blurred = cv2.GaussianBlur(noisy_img, (3, 3), 0)
    
    # 3. Threshold back to binary
    # This creates the "rough edge" effect where the noise crossed the threshold
    _, rough = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)
    
    return rough

    return rough

def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype = "float32")
    
    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def detect_and_warp_grid(img: np.ndarray) -> np.ndarray:
    # 1. Preprocess
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    # Adaptive threshold to handle uneven lighting
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # 2. Find Contours
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 3. Filter for the grid
    # We expect a large rectangle with specific aspect ratio
    # Grid is 7.5" x 5.5" => AR = 1.36
    grid_cnt = None
    max_area = 0
    
    # Debug visualization
    debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    for c in cnts:
        area = cv2.contourArea(c)
        if area < 50000: # Filter small noise (grid should be large)
            continue
            
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # If it has 4 points, it's a candidate
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            ar = w / float(h)
            
            # Draw all candidates in red
            cv2.drawContours(debug_img, [approx], -1, (0, 0, 255), 2)
            
            # Check AR (allow some perspective distortion)
            if 1.0 < ar < 1.8:
                if area > max_area:
                    max_area = area
                    grid_cnt = approx
    
    # Save debug image
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    debug_dir = os.path.join(base_dir, "generated")
    os.makedirs(debug_dir, exist_ok=True)
    
    if grid_cnt is not None:
        cv2.drawContours(debug_img, [grid_cnt], -1, (0, 255, 0), 4)
        
    cv2.imwrite(os.path.join(debug_dir, "debug_detection.jpg"), debug_img)
                
    if grid_cnt is None:
        # Fallback: if no clear grid found, return original (maybe user cropped it perfectly?)
        print("Warning: No grid detected, using original image")
        return img
        
    # 4. Perspective Transform
    # Get 4 corners
    pts = grid_cnt.reshape(4, 2)
    rect = order_points(pts)
    
    # Target dimensions (fixed size for 7x9 grid)
    # 9 cols * 250px = 2250
    # 7 rows * 250px = 1750
    # This gives us nice square-ish cells
    dst_w, dst_h = 2250, 1750
    
    dst = np.array([
        [0, 0],
        [dst_w - 1, 0],
        [dst_w - 1, dst_h - 1],
        [0, dst_h - 1]], dtype = "float32")
        
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (dst_w, dst_h))
    
    cv2.imwrite(os.path.join(debug_dir, "debug_warped.jpg"), warped)
    
    return warped

from pdf2image import convert_from_bytes

def extract_glyphs(img_bytes: bytes) -> dict:
    # Check if PDF
    if img_bytes.startswith(b'%PDF'):
        # Convert first page to image
        images = convert_from_bytes(img_bytes)
        if not images:
            raise ValueError("Empty PDF")
        # Take first page
        pil_img = images[0].convert('L') # Grayscale
        img = np.array(pil_img)
    else:
        # Decode image
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Could not decode image")

    # Detect and warp grid
    # This handles rotation, skew, and margins
    warped = detect_and_warp_grid(img)
    
    # Threshold the warped image for character extraction
    # (Inverted: Text is white, background black)
    _, binary = cv2.threshold(warped, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Grid logic
    h, w = warped.shape
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
        
        # Apply roughness filter to simulate penmanship
        roi_inv = roughen_glyph(roi_inv)
        
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
