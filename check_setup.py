import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Check Tesseract
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print("--- ENVIRONMENT CHECK ---")
print(f"1. Checking Tesseract OCR: {'FOUND' if os.path.exists(tesseract_path) else 'NOT FOUND'}")

# Check Poppler
poppler_paths = [
    os.path.join(CURRENT_DIR, r'poppler\Library\bin'),
    os.path.join(CURRENT_DIR, r'poppler\bin'),
    os.path.join(CURRENT_DIR, r'poppler\Release-24.08.0-0\Library\bin'),
    r'C:\Program Files\poppler\Library\bin'
]

poppler_found = False
for p in poppler_paths:
    if os.path.exists(p) and os.path.exists(os.path.join(p, "pdftoppm.exe")):
        print(f"2. Checking Poppler: FOUND at {p}")
        poppler_found = True
        break

if not poppler_found:
    print("2. Checking Poppler: NOT FOUND")
    print(f"   Please extract Poppler so that 'pdftoppm.exe' sits inside: {os.path.join(CURRENT_DIR, 'poppler', 'Library', 'bin')}")