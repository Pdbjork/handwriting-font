from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
import os

def make_font(svg_map: dict, job_id: str) -> str:
    # Output directory
    # We'll save to a 'generated' folder that main.py can serve
    out_dir = "/code/backend/app/generated"
    os.makedirs(out_dir, exist_ok=True)
    out_filename = f"{job_id}.ttf"
    out_path = os.path.join(out_dir, out_filename)
    
    # Setup FontBuilder
    units_per_em = 1000
    fb = FontBuilder(units_per_em, isTTF=True)
    
    # Map chars to glyph names
    # .notdef is required
    # Sort keys for stability
    chars = sorted(svg_map.keys())
    glyph_order = ['.notdef'] + chars
    fb.setupGlyphOrder(glyph_order)
    
    # Map chars to unicode
    cmap = {ord(c): c for c in chars}
    fb.setupCharacterMap(cmap)
    
    # Create glyphs
    glyphs = {}
    metrics = {}
    
    # .notdef (empty box)
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 800))
    pen.lineTo((500, 800))
    pen.lineTo((500, 0))
    pen.closePath()
    glyphs['.notdef'] = pen.glyph()
    metrics['.notdef'] = (600, 50)
    
    for char in chars:
        svg_d = svg_map[char]
        pen = TTGlyphPen(None)
        
        try:
            # Parse SVG path - don't call parse_path, just skip for now
            # The SVG path data needs proper transformation
            # For MVP, create simple placeholder glyphs
            pass
            
        except Exception as e:
            print(f"Error tracing {char}: {e}")
            
        glyphs[char] = pen.glyph()
        # Fixed width for now
        metrics[char] = (600, 0)
        
    # Setup tables
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    
    # Name table - remove uniqueID as it's not a standard field
    name_strings = dict(
        familyName="Handwriting",
        styleName="Regular",
        fullName=f"Handwriting {job_id}",
        version="Version 1.0",
        psName=f"Handwriting-{job_id}"
    )
    fb.setupNameTable(name_strings)
    
    # OS/2 table
    fb.setupOS2(sTypoAscender=800, usWinAscent=800, usWinDescent=200)
    
    # Post table
    fb.setupPost()
    
    # Save
    fb.save(out_path)
    
    # Return URL path (relative to API root)
    return f"/download/{out_filename}"
