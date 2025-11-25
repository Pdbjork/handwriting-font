import cv2
import numpy as np
import os

def create_dummy_char():
    # Create a white canvas (black text on white)
    img = np.ones((200, 200), dtype=np.uint8) * 255
    
    # Draw a thick letter 'A'
    # Left leg
    cv2.line(img, (100, 20), (40, 180), 0, 15)
    # Right leg
    cv2.line(img, (100, 20), (160, 180), 0, 15)
    # Crossbar
    cv2.line(img, (60, 120), (140, 120), 0, 15)
    
    return img

def roughen_glyph(img):
    # Input: Grayscale image (0=black ink, 255=white paper)
    
    h, w = img.shape
    
    # 1. Add noise to edges
    # Create random noise
    noise = np.random.normal(0, 10, (h, w)).astype(np.int16)
    
    # Add noise to image (convert to int16 to avoid overflow)
    noisy_img = img.astype(np.int16) + noise
    noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
    
    # 2. Erosion/Dilation (Morphology)
    # "Ink bleed" - Dilation expands the black regions (erodes the white)
    # But first, let's make the edges irregular
    
    kernel = np.ones((3,3), np.uint8)
    
    # Erode (thins black lines if we think in white-foreground, but here 0 is ink)
    # In OpenCV:
    # erode: erodes bright areas (white paper) -> expands dark areas (ink bleed)
    # dilate: expands bright areas (white paper) -> shrinks dark areas (dried ink)
    
    # Let's try a sequence to make it organic
    # 1. Slight blur to soften
    blurred = cv2.GaussianBlur(noisy_img, (3, 3), 0)
    
    # 2. Threshold back to binary to get "rough" edges from the noise+blur
    _, rough = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)
    
    # 3. Morphological close (dilate then erode) to fill small holes
    # rough = cv2.morphologyEx(rough, cv2.MORPH_CLOSE, kernel)
    
    # 4. Random erosion/dilation to vary line width slightly? 
    # Maybe just the noise+blur+threshold is enough for "rough edges"
    
    return rough

if __name__ == "__main__":
    original = create_dummy_char()
    processed = roughen_glyph(original)
    
    # Save for inspection
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cv2.imwrite(os.path.join(base_dir, "test_original.png"), original)
    cv2.imwrite(os.path.join(base_dir, "test_rough.png"), processed)
    
    print(f"Saved test images to {base_dir}")
