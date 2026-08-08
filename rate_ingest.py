import os
import sys
import sqlite3
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import pdfplumber
import pandas as pd
import config

HAS_OCR = False
POPPLER_PATH = None

def find_pdftoppm():
    standard_paths = [
        os.path.join(CURRENT_DIR, r'poppler\Library\bin'),
        os.path.join(CURRENT_DIR, r'poppler\bin'),
        os.path.join(CURRENT_DIR, r'poppler-24.08.0\Library\bin'),
        r'C:\Program Files\poppler\Library\bin',
        r'C:\Program Files\poppler\bin'
    ]
    for path in standard_paths:
        if os.path.exists(os.path.join(path, "pdftoppm.exe")):
            return path
            
    for root, dirs, files in os.walk(CURRENT_DIR):
        if "pdftoppm.exe" in files:
            return root
    return None

try:
    from pdf2image import convert_from_path
    import pytesseract

    tesseract_possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.path.expanduser('~'), r'AppData\Local\Tesseract-OCR\tesseract.exe')
    ]
    for path in tesseract_possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

    POPPLER_PATH = find_pdftoppm()
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT UNIQUE,
            description TEXT,
            unit TEXT,
            standard_rate REAL,
            source_file TEXT
        )
    """)
    conn.commit()
    conn.close()


def extract_text_with_ocr(pdf_path):
    """OCR engine that scans ALL pages of the rate book."""
    if not HAS_OCR or not POPPLER_PATH:
        print("\n[ERROR] Poppler path was not located.")
        return []

    print("\nScanned PDF detected. Running local OCR engine...")
    print(f"Using Poppler path: {POPPLER_PATH}")

    extracted_lines = []
    
    try:
        # Convert all pages without hardcoded page limit
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        total_imgs = len(images)
        print(f"Successfully loaded ALL {total_imgs} pages for full OCR ingestion.")

        for idx, img in enumerate(images, start=1):
            if idx % 10 == 0 or idx == total_imgs:
                print(f"  --> OCR scanning page {idx} of {total_imgs}...")
            
            page_text = pytesseract.image_to_string(img)
            for line in page_text.split('\n'):
                line_str = line.strip()
                if line_str:
                    extracted_lines.append(line_str)

    except Exception as e:
        print(f"\n[OCR ERROR]: {e}")

    return extracted_lines


def parse_rate_pdf(pdf_path):
    extracted_rows = []
    filename = os.path.basename(pdf_path)
    print(f"\nProcessing Rate Schedule PDF: {filename}...")

    has_text = False
    with pdfplumber.open(pdf_path) as pdf:
        sample_page = min(5, len(pdf.pages))
        text_sample = pdf.pages[sample_page - 1].extract_text()
        if text_sample and len(text_sample.strip()) > 50:
            has_text = True

    if has_text:
        print("Digital PDF structure detected. Extracting searchable text...")
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    for line in text.split("\n"):
                        if line.strip():
                            extracted_rows.append(line.strip())
    else:
        extracted_rows = extract_text_with_ocr(pdf_path)

    structured_items = []
    
    # Enhanced regex for CPWD DSR formats (e.g. 2.1, 2.1.1, 14.2.1A, 2.8.1.1)
    dsr_pattern = re.compile(r'^(\d+\.\d+(?:\.\d+)*(?:[A-Za-z])?)\s+(.*)')

    for line in extracted_rows:
        match = dsr_pattern.search(line)
        if match:
            item_code = match.group(1)
            rest_of_line = match.group(2)
            
            # Find decimal/float rate value at end of line if present
            rate_val = 0.0
            numbers = re.findall(r'\d+(?:\.\d+)?', rest_of_line)
            if numbers:
                try:
                    rate_val = float(numbers[-1])
                except ValueError:
                    rate_val = 0.0
            
            structured_items.append({
                "item_code": item_code,
                "description": rest_of_line,
                "unit": "",
                "rate": rate_val
            })

    print(f"Extraction finished for {filename}. Found {len(structured_items)} structured entries.")
    return structured_items


def process_all_rate_books():
    init_db()
    pdf_files = [f for f in os.listdir(config.RATE_BOOKS_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF rate books found in '{config.RATE_BOOKS_DIR}'. Place your rate PDFs there.")
        return

    for pdf_file in pdf_files:
        full_path = os.path.join(config.RATE_BOOKS_DIR, pdf_file)
        items = parse_rate_pdf(full_path)
        
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()
        saved_count = 0

        for item in items:
            code = item["item_code"]
            desc = item["description"]
            unit = item["unit"]
            rate_val = item["rate"]

            try:
                cursor.execute("""
                    INSERT INTO rate_schedule (item_code, description, unit, standard_rate, source_file)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(item_code) DO UPDATE SET
                        description=excluded.description,
                        unit=excluded.unit,
                        standard_rate=excluded.standard_rate,
                        source_file=excluded.source_file
                """, (code, desc, unit, rate_val, pdf_file))
                saved_count += 1
            except Exception as e:
                pass

        conn.commit()
        conn.close()
        print(f"Database updated with {saved_count} rate items from {pdf_file}.\n")


if __name__ == "__main__":
    process_all_rate_books()