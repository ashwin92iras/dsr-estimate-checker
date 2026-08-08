import os
import sys
import sqlite3
import streamlit as st

# Path setup for Streamlit Cloud environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")

st.set_page_config(page_title="CPWD DSR Estimate Checker", layout="wide")

st.title("🏗️ CPWD DSR Estimate Rate Checker")

# Sidebar Status
st.sidebar.header("Database Info")
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rate_schedule")
        count = cursor.fetchone()[0]
        conn.close()
        st.sidebar.success(f"DSR Items Ingested: **{count}**")
    except Exception as e:
        st.sidebar.error(f"Database Read Error: {e}")
else:
    st.sidebar.warning("`database.db` not detected in `/data` folder.")

st.write("Upload contractor estimate files (Excel or CSV) to verify rates against standard CPWD DSR schedules.")

uploaded_file = st.file_uploader("Upload Contractor Estimate File", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        import checker_engine

        os.makedirs(DATA_DIR, exist_ok=True)
        temp_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.subheader("Analyzing Estimate...")
        results_df = checker_engine.analyze_estimate_file(temp_path)

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
                file_name="Estimate_Audit_Report.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error analyzing estimate: {e}")