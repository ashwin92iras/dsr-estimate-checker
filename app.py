import os
import sys
import sqlite3
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")

st.set_page_config(page_title="CPWD DSR Estimate Checker", layout="wide")
st.title("🏗️ CPWD DSR Estimate Rate Checker")

# --- Database & Schedule Loader ---
def get_available_schedules():
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT schedule_name FROM rate_schedule ORDER BY schedule_name DESC")
        schedules = [row[0] for row in cursor.fetchall()]
        conn.close()
        return schedules
    except Exception:
        return []

schedules = get_available_schedules()

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Reference Settings")

if schedules:
    selected_schedule = st.sidebar.selectbox("Select Target Rate Schedule:", schedules)
    
    # Fetch item count for selected schedule
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rate_schedule WHERE schedule_name = ?", (selected_schedule,))
    item_count = cursor.fetchone()[0]
    conn.close()
    
    st.sidebar.success(f"Active Schedule: **{selected_schedule}**\nLoaded Items: **{item_count}**")
else:
    selected_schedule = None
    st.sidebar.warning("No reference schedules found in database. Run `ingest_schedules.py` first.")

st.write("Upload contractor estimate files (Excel or CSV) to verify items and rates against standard reference schedules.")

# --- File Uploader & Analysis ---
uploaded_file = st.file_uploader("Upload Contractor Estimate File", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    if not selected_schedule:
        st.error("Please select or load a valid Reference Schedule from the sidebar first!")
    else:
        try:
            import checker_engine

            os.makedirs(DATA_DIR, exist_ok=True)
            temp_path = os.path.join(DATA_DIR, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.subheader(f"Analyzing Estimate against [{selected_schedule}]...")
            
            # Pass selected_schedule into checker_engine
            results_df = checker_engine.analyze_estimate_file(temp_path, schedule_name=selected_schedule)

            if results_df is not None and not results_df.empty:
                overcharged_count = len(results_df[results_df['Status'] == 'OVERCHARGED'])
                ok_count = len(results_df[results_df['Status'] == 'OK'])
                not_found_count = len(results_df[results_df['Status'] == 'NOT FOUND'])

                col1, col2, col3 = st.columns(3)
                col1.metric("Verified Items (OK)", ok_count)
                col2.metric("Rate Discrepancies", overcharged_count, delta_color="inverse")
                col3.metric("Items Not Found in DSR", not_found_count)

                st.subheader("Detailed Analysis Results")

                def highlight_status(val):
                    if val == 'OVERCHARGED':
                        return 'background-color: #ffcccc; color: red; font-weight: bold;'
                    elif val == 'UNDERCHARGED':
                        return 'background-color: #ffffcc; color: brown;'
                    elif val == 'OK':
                        return 'background-color: #e6ffe6; color: green;'
                    return ''

                st.dataframe(results_df.style.map(highlight_status, subset=['Status']), use_container_width=True)

                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Audit Report (CSV)",
                    data=csv,
                    file_name=f"Audit_Report_{selected_schedule}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error during analysis: {e}")