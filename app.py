import streamlit as st
from pathlib import Path

# Get the absolute path to this script's directory
SCRIPT_DIR = Path(__file__).parent.resolve()

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Our Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
from database.init_db import init_database
if not Path("expenses.db").exists():
    with st.spinner("Initializing database..."):
        init_database()

# Get user names from database (safe - returns strings, not SQLAlchemy objects)
from database.crud import get_user_names
user_names = get_user_names()

if "current_user" not in st.session_state:
    st.session_state.current_user = user_names[0] if user_names else "You"

# Get user ID for queries
from database.crud import get_user_id_by_name
st.session_state.current_user_id = get_user_id_by_name(st.session_state.current_user) or 0

# Define all pages using st.Page with absolute paths
page_log_expense = st.Page(
    str(SCRIPT_DIR / "ui/pages/1_📝_Log_Expense.py"),
    title="📝 Log Expense",
    icon="📊",
    default=True
)
page_dashboard = st.Page(str(SCRIPT_DIR / "ui/pages/2_📊_Dashboard.py"), title="📊 Dashboard", icon="📈")
page_monthly_summary = st.Page(str(SCRIPT_DIR / "ui/pages/3_📈_Monthly_Summary.py"), title="📈 Monthly Summary", icon="💰")
page_settings = st.Page(str(SCRIPT_DIR / "ui/pages/4_⚙️_Settings.py"), title="⚙️ Settings", icon="⚙️")
page_users = st.Page(str(SCRIPT_DIR / "ui/pages/5_👥_Users.py"), title="👥 Users", icon="👤")

# --- Navigation ---
pg = st.navigation({
    "📊 Core": [page_log_expense, page_dashboard, page_monthly_summary],
    "⚙️ Management": [page_settings, page_users],
})

# Run navigation - this switches to the selected page
pg.run()