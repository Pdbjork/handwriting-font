import sys
import os
import cv2
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.tracing import extract_glyphs

def create_dummy_grid():
    # Create a white canvas
    h, w = 2000, 2000
    img = np.ones((h, w), dtype=np.uint8) * 255
    
    # Draw grid lines (optional, logic assumes fixed cell size)
    # Just draw a letter 'A' in the first cell
    # Cell size is roughly w/9 x h/7
    cell_w = w // 9
    cell_h = h // 7
    
    # Draw 'A' in first cell (0,0)
    # Center of first cell
    cx, cy = cell_w // 2, cell_h // 2
    
    # Draw thick 'A'
    cv2.putText(img, "A", (cx-50, cy+50), cv2.FONT_HERSHEY_SIMPLEX, 5, (0), 10)
    
    # Encode to bytes
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()

def test_tracing():
    print("Testing tracing service...")
    
    try:
        img_bytes = create_dummy_grid()
        
        # Run extraction
        # This will call roughen_glyph internally
        results = extract_glyphs(img_bytes)
        
        print(f"Extracted {len(results)} glyphs")
        
        if 'A' in results:
            print("SUCCESS: Extracted glyph 'A'")
            # print(f"SVG Path: {results['A'][:50]}...")
            return True
        else:
            print("ERROR: Did not extract 'A'")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tracing()
    sys.exit(0 if success else 1)
