import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import pdfplumber
import config

pdf_path = os.path.join(config.RATE_BOOKS_DIR, "DSR_Vol_1_Civil_comp.pdf")

if not os.path.exists(pdf_path):
    print("File not found at:", pdf_path)
    sys.exit(1)

print("--- INSPECTING PDF STRUCTURE ---")
with pdfplumber.open(pdf_path) as pdf:
    # Read page 15 or 20 where actual DSR items typically begin
    sample_page_num = min(20, len(pdf.pages))
    page = pdf.pages[sample_page_num - 1]
    
    print(f"\n[RAW TEXT FROM PAGE {sample_page_num}]:\n")
    text = page.extract_text()
    if text:
        # Print first 25 lines of the page
        lines = text.split("\n")[:25]
        for idx, line in enumerate(lines, 1):
            print(f"Line {idx:02d}: {line}")
    else:
        print("No text found on this page.")