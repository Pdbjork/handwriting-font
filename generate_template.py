#!/usr/bin/env python3
"""Generate a handwriting template PDF with a 7x9 grid."""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_template(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 0.5*inch, "Handwriting Font Template")
    
    # Instructions
    c.setFont("Helvetica", 10)
    instructions = [
        "Instructions:",
        "1. Print this template",
        "2. Write each character clearly in its box using a dark pen",
        "3. Scan the completed template at 300 DPI or higher",
        "4. Upload the scan to generate your custom font"
    ]
    y = height - inch
    for line in instructions:
        c.drawString(0.5*inch, y, line)
        y -= 0.15*inch
    
    # Grid parameters
    rows = 7
    cols = 9
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    
    # Calculate cell size
    grid_width = 7.5 * inch
    grid_height = 5.5 * inch
    cell_width = grid_width / cols
    cell_height = grid_height / rows
    
    # Starting position (centered)
    start_x = (width - grid_width) / 2
    start_y = height - 3*inch
    
    # Draw grid
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)
    
    char_index = 0
    for row in range(rows):
        for col in range(cols):
            if char_index >= len(chars):
                break
                
            x = start_x + col * cell_width
            y = start_y - row * cell_height
            
            # Draw cell border
            c.rect(x, y - cell_height, cell_width, cell_height)
            
            # Draw character label (small, in corner)
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(x + 2, y - 10, chars[char_index])
            
            char_index += 1
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawCentredString(width/2, 0.5*inch, "Write each character in the center of its box")
    
    c.save()
    print(f"Template created: {filename}")

if __name__ == "__main__":
    create_template("backend/app/assets/template.pdf")
