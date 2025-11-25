from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.svgLib.path import parse_path
import os

def make_font(svg_map: dict, job_id: str) -> str:
    # Output directory
    # We'll save to a 'generated' folder that main.py can serve
    # Use relative path to avoid hardcoded /code
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, "generated")
    os.makedirs(out_dir, exist_ok=True)
    out_filename = f"{job_id}.otf"
    out_path = os.path.join(out_dir, out_filename)
    
    # Setup FontBuilder
    units_per_em = 1000
    fb = FontBuilder(units_per_em, isTTF=False)
    
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
    charStrings = {}
    metrics = {}
    
    # .notdef (empty box)
    pen = T2CharStringPen(600, None)
    pen.moveTo((100, 0))
    pen.lineTo((100, 800))
    pen.lineTo((500, 800))
    pen.lineTo((500, 0))
    pen.closePath()
    charStrings['.notdef'] = pen.getCharString()
    metrics['.notdef'] = (600, 50)
    
    for char in chars:
        svg_d = svg_map[char]
        pen = T2CharStringPen(600, None)
        
        try:
            # Parse SVG path
            # The SVG path data needs proper transformation
            # SVG is y-down, Font is y-up
            # We also need to scale/translate to fit the em square
            
            # We'll use a transform pen to do the flipping/scaling
            from fontTools.pens.transformPen import TransformPen
            
            # Calculate bounds if possible, or just use fixed scale
            # Let's try a fixed scale for now, assuming the input is reasonable
            # Flip Y: (1, 0, 0, -1, 0, 0)
            # Translate Y up: (1, 0, 0, -1, 0, 800)
            
            # We need to draw the path_obj into our 'pen' (T2CharStringPen)
            # But we want to transform it first.
            tpen = TransformPen(pen, (1, 0, 0, -1, 0, 750)) # Flip Y and move up

            # 1. Parse and draw directly into the transform pen
            # parse_path(path_d, pen)
            parse_path(svg_d, tpen)
            
        except Exception as e:
            print(f"Error tracing {char}: {e}")
            
        charStrings[char] = pen.getCharString()
        # Fixed width for now
        metrics[char] = (600, 0)
        
    # Name table - remove uniqueID as it's not a standard field
    name_strings = dict(
        familyName="Handwriting",
        styleName="Regular",
        fullName=f"Handwriting {job_id}",
        version="Version 1.0",
        psName=f"Handwriting-{job_id}"
    )
    fb.setupNameTable(name_strings)
    
    # Setup tables
    fontInfo = {
        'FamilyName': name_strings['familyName'],
        'FullName': name_strings['fullName'],
        'Weight': 'Regular',
    }
    privateDict = {}
    fb.setupCFF(psName=name_strings['psName'], charStringsDict=charStrings, fontInfo=fontInfo, privateDict=privateDict)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    
    # OS/2 table
    fb.setupOS2(sTypoAscender=800, usWinAscent=800, usWinDescent=200)
    
    # Post table
    fb.setupPost()
    
    # Save
    fb.save(out_path)
    
    # Return URL path (relative to API root)
    return f"/download/{out_filename}"
