import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
RATE_BOOKS_DIR = os.path.join(DATA_DIR, "rate_books")
DB_PATH = os.path.join(DATA_DIR, "database.db")

# Discrepancy Thresholds
RATE_DISCREPANCY_THRESHOLD_PCT = 5.0  # Flag if claimed rate differs by > 5%
FUZZY_MATCH_THRESHOLD = 70.0  # Fuzzy matching score cutoff (0-100)

# Ensure folders exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RATE_BOOKS_DIR, exist_ok=True)