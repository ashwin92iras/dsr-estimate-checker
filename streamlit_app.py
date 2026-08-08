import os
import sys

# If running directly under Python/Uvicorn, spawn native Streamlit CLI
if "streamlit" not in sys.modules and "--server.port" not in sys.argv:
    os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:])

# Main App Code Execution
import app