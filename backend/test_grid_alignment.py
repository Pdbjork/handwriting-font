import cv2
import numpy as np
import os

def create_dummy_scan(rotated=False):
    # Create a white canvas (simulating A4/Letter)
    h, w = 3300, 2550 # 300 DPI Letter
    img = np.ones((h, w), dtype=np.uint8) * 255
    
    # Draw grid lines (7 rows, 9 cols)
    # Margins from generate_template.py:
    # grid_width = 7.5 * inch = 2250 px
    # grid_height = 5.5 * inch = 1650 px
    # start_x = (width - grid_width) / 2 = (2550 - 2250)/2 = 150
    # start_y = height - 3*inch = 3300 - 900 = 2400 (bottom Y in PDF coords)
    # In image coords (y=0 top), start_y is roughly 3300 - 2400 = 900? 
    # Let's approximate margins: top 300, left 150
    
    margin_top = 600
    margin_left = 150
    cell_w = 2250 // 9
    cell_h = 1650 // 7
    
    # Draw 'A' in first cell
    # Main letter (Center)
    cv2.putText(img, "A", (margin_left + 50, margin_top + 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0), 5)
    
    # Guide letter (Top-Left)
    # Simulate the small 'A' in the corner
    cv2.putText(img, "A", (margin_left + 10, margin_top + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0), 1)
    
    # Draw grid borders
    for r in range(8):
        y = margin_top + r * cell_h
        cv2.line(img, (margin_left, y), (margin_left + 9*cell_w, y), 0, 2)
        
    for c in range(10):
        x = margin_left + c * cell_w
        cv2.line(img, (x, margin_top), (x, margin_top + 7*cell_h), 0, 2)
        
    if rotated:
        # Rotate image by 2 degrees to simulate bad scan
        center = (w//2, h//2)
        M = cv2.getRotationMatrix2D(center, 2, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderValue=255)
        
    return img

from app.services.tracing import detect_and_warp_grid

def test_slicing(img):
    # Apply detection first
    warped = detect_and_warp_grid(img)
    
    # Current logic from tracing.py
    h, w = warped.shape
    rows = 7
    cols = 9
    cell_w = w // cols
    cell_h = h // rows
    
    # Extract first cell (A)
    r, c = 0, 0
    x = c * cell_w
    y = r * cell_h
    
    pad_x = int(cell_w * 0.1)
    pad_y = int(cell_h * 0.1)
    
    roi = warped[y+pad_y : y+cell_h-pad_y, x+pad_x : x+cell_w-pad_x]
    
    # Check if we captured the 'A' (black pixels)
    # Invert for counting
    _, binary = cv2.threshold(roi, 128, 255, cv2.THRESH_BINARY_INV)
    non_zero = cv2.countNonZero(binary)
    
    print(f"Non-zero pixels in cell 0,0: {non_zero}")
    return roi

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test 1: Perfect alignment (should fail because current logic assumes NO margins)
    print("Testing perfect scan (with margins)...")
    perfect = create_dummy_scan(rotated=False)
    roi_perfect = test_slicing(perfect)
    cv2.imwrite(os.path.join(base_dir, "debug_perfect_slice.png"), roi_perfect)
    
    # Test 2: Rotated
    print("Testing rotated scan...")
    rotated = create_dummy_scan(rotated=True)
    roi_rotated = test_slicing(rotated)
    cv2.imwrite(os.path.join(base_dir, "debug_rotated_slice.png"), roi_rotated)
