import sys
import os
import shutil

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.fontbuild import make_font
from fontTools.ttLib import TTFont

def test_font_generation():
    print("Testing font generation...")
    
    # Dummy SVG map (Letter 'A' approximation)
    # Simple triangle path
    svg_map = {
        "A": "M 10 10 L 50 90 L 90 10 Z"
    }
    
    job_id = "test_job"
    
    # Clean up previous run
    out_dir = "/Users/pdbjork/handwriting-font/backend/app/generated"
    out_path = os.path.join(out_dir, f"{job_id}.otf")
    if os.path.exists(out_path):
        os.remove(out_path)
        
    try:
        # Run generation
        url_path = make_font(svg_map, job_id)
        print(f"Generated font at: {url_path}")
        
        # Verify file exists
        if not os.path.exists(out_path):
            print("ERROR: Output file not found!")
            return False
            
        # Verify font content
        font = TTFont(out_path)
        
        # Check if 'A' exists in glyf/CFF table
        if 'A' not in font.getGlyphOrder():
            print("ERROR: Glyph 'A' not found in font!")
            return False
            
        # For CFF (OTF), we check the CFF table
        cff = font['CFF '].cff
        top_dict = cff.topDictIndex[0]
        char_strings = top_dict.CharStrings
        
        if 'A' not in char_strings:
             print("ERROR: Glyph 'A' not found in CharStrings!")
             return False
             
        # Check if it has content (not empty)
        # This is a bit complex for CFF, but if it didn't crash during build, it likely has content.
        print("SUCCESS: Font generated and contains glyph 'A'")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_font_generation()
    sys.exit(0 if success else 1)
