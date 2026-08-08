import os

# ==========================================
# FILE PATHS & DIRECTORIES
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RATE_BOOKS_DIR = os.path.join(DATA_DIR, "rate_books")
DB_PATH = os.path.join(DATA_DIR, "database.db")

# Ensure required folders exist
os.makedirs(RATE_BOOKS_DIR, exist_ok=True)

# ==========================================
# MATCHING THRESHOLDS & ENGINE SETTINGS
# ==========================================
FUZZY_MATCH_THRESHOLD = 60.0
TOP_K_CANDIDATES = 3
RATE_DISCREPANCY_THRESHOLD_PCT = 5.0

# ==========================================
# WEB / NETWORK HOSTING CONFIGURATION
# ==========================================
WEB_HOST = "0.0.0.0"
WEB_PORT = 8501

# ==========================================
# STANDARD COLUMN NAME MAPPINGS
# ==========================================
COLUMN_ITEM_CODE = "item_code"
COLUMN_DESCRIPTION = "description"
COLUMN_RATE = "rate"
COLUMN_UNIT = "unit"