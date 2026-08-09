import os
import sqlite3
import pandas as pd
from rapidfuzz import process, fuzz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")

def clean_column_names(df):
    cols = [str(col).strip().lower() for col in df.columns]
    mapping = {}
    for original, clean in zip(df.columns, cols):
        if any(k in clean for k in ['item', 'code', 'no', 'dsr_no', 'ussor_no']):
            mapping[original] = 'item_number'
        elif any(k in clean for k in ['desc', 'particular', 'description', 'specification']):
            mapping[original] = 'description'
        elif any(k in clean for k in ['rate', 'quoted', 'contractor_rate', 'unit_rate', 'estimated_rate']):
            mapping[original] = 'quoted_rate'
        elif any(k in clean for k in ['unit', 'per']):
            mapping[original] = 'unit'
    return df.rename(columns=mapping)

def get_multi_schedule_data(schedule_names):
    """Fetches reference schedule items for all requested schedule names."""
    if not os.path.exists(DB_PATH) or not schedule_names:
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    placeholders = ','.join(['?'] * len(schedule_names))
    query = f"""
        SELECT item_number, description, rate AS standard_rate, unit AS standard_unit, schedule_name 
        FROM rate_schedule 
        WHERE schedule_name IN ({placeholders})
    """
    df_ref = pd.read_sql_query(query, conn, params=schedule_names)
    conn.close()

    if not df_ref.empty:
        df_ref['item_number'] = df_ref['item_number'].astype(str).str.strip()
        df_ref['description_clean'] = df_ref['description'].astype(str).str.lower().str.strip()
    return df_ref

def analyze_estimate_file(file_path, schedule_names):
    if file_path.endswith('.csv'):
        df_est = pd.read_csv(file_path)
    else:
        df_est = pd.read_excel(file_path)

    df_est = clean_column_names(df_est)

    if 'item_number' not in df_est.columns or 'quoted_rate' not in df_est.columns:
        raise ValueError("Uploaded file must contain 'item_number' and 'quoted_rate' columns.")

    df_ref = get_multi_schedule_data(schedule_names)
    if df_ref.empty:
        raise ValueError("No matching reference data found in database.db for selected schedules.")

    results = []

    for _, row in df_est.iterrows():
        raw_item_no = str(row.get('item_number', '')).strip()
        quoted_rate = pd.to_numeric(row.get('quoted_rate', 0), errors='coerce') or 0.0
        est_desc = str(row.get('description', '')).strip()

        matched_item = None
        std_rate = None
        std_unit = None
        std_desc = None
        matched_sched = None
        status = 'NOT FOUND'
        rate_diff = 0.0

        # 1. Priority Exact Search by Item Code across selected schedules
        match_rows = df_ref[df_ref['item_number'] == raw_item_no]
        
        if not match_rows.empty:
            matched_row = match_rows.iloc[0] # Pick primary matching schedule
            std_rate = float(matched_row['standard_rate'])
            std_unit = matched_row['standard_unit']
            std_desc = matched_row['description']
            matched_sched = matched_row['schedule_name']
            matched_item = raw_item_no
        else:
            # 2. Fuzzy Description Fallback
            if est_desc and len(est_desc) > 5:
                ref_descriptions = df_ref['description_clean'].tolist()
                best_match = process.extractOne(
                    est_desc.lower(), 
                    ref_descriptions, 
                    scorer=fuzz.WRatio
                )
                if best_match and best_match[1] >= 75:
                    matched_row = df_ref.iloc[best_match[2]]
                    matched_item = matched_row['item_number']
                    std_rate = float(matched_row['standard_rate'])
                    std_unit = matched_row['standard_unit']
                    std_desc = matched_row['description']
                    matched_sched = matched_row['schedule_name']

        # Determine Audit Status
        if std_rate is not None:
            rate_diff = round(quoted_rate - std_rate, 2)
            if rate_diff > 0.01:
                status = 'OVERCHARGED'
            elif rate_diff < -0.01:
                status = 'UNDERCHARGED'
            else:
                status = 'OK'

        results.append({
            'Item No': raw_item_no,
            'Description': est_desc,
            'Quoted/Est Rate (₹)': quoted_rate,
            'Standard Rate (₹)': std_rate if std_rate is not None else 'N/A',
            'Unit': std_unit if std_unit else 'N/A',
            'Variance (₹)': rate_diff if std_rate is not None else 'N/A',
            'Status': status,
            'Matched Schedule Source': matched_sched if matched_sched else 'NOT FOUND',
            'Matched Code': matched_item if matched_item else 'N/A',
            'Standard Specification': std_desc if std_desc else 'N/A'
        })

    return pd.DataFrame(results)