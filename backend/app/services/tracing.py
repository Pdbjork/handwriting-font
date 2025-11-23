import cv2
import numpy as np
import potrace

def extract_glyphs(img_bytes: bytes) -> dict:
    # Decode image
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        raise ValueError("Could not decode image")

    # Threshold (Inverted: Text is white, background black)
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Find contours to detect grid cells
    # We assume the template has visible boxes.
    # If not, we might need a different strategy (e.g. fixed grid slicing).
    # For now, let's assume we just find connected components which are likely the letters themselves 
    # if the user cropped them, OR we find the boxes.
    
    # Better strategy for MVP without known template:
    # Just find all contours, assume they are letters, sort them reading-order.
    # This is risky if there are noise or box lines.
    
    # Let's assume the user uploads a clean scan of the template.
    # We'll try to find the grid boxes.
    # In a real app, we'd probably use ArUco markers or a strict template.
    
    # Fallback: Fixed grid slicing.
    # Assume the image is the template.
    # Grid: 7 rows, 9 cols? (63 chars)
    # Charset: A-Z, a-z, 0-9 (62 chars)
    
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
        # Add some padding to avoid border lines if they exist
        pad_x = int(cell_w * 0.1)
        pad_y = int(cell_h * 0.1)
        
        roi = binary[y+pad_y : y+cell_h-pad_y, x+pad_x : x+cell_w-pad_x]
        
        # Check if empty
        if cv2.countNonZero(roi) == 0:
            continue
            
        # Trace
        # Create a bitmap from the binary ROI
        # Potrace expects 0/1, we have 0/255
        bmp = potrace.Bitmap(roi / 255.0)
        path = bmp.trace()
        
        if not path:
            continue
            
        svg_d = []
        for curve in path:
            start = curve.start_point
            svg_d.append(f"M {start.x} {start.y}")
            for segment in curve:
                if segment.is_corner:
                    c = segment.c
                    end = segment.end_point
                    svg_d.append(f"L {c.x} {c.y} L {end.x} {end.y}")
                else:
                    c1 = segment.c1
                    c2 = segment.c2
                    end = segment.end_point
                    svg_d.append(f"C {c1.x} {c1.y} {c2.x} {c2.y} {end.x} {end.y}")
            svg_d.append("Z")
            
        results[char] = " ".join(svg_d)
        
    return results
