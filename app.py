import os
import subprocess
import streamlit as st
from views import poll, current, history, debts, morosos, statistics
from utils import load_users, init_db, current_debts_is_empty, init_current_debts_from_yaml
import time


# Inputs directory
USERS_FILE = "inputs/users.yaml"  # Users, initial debts, and description

# History directory (kept for session-file path passing; history data lives in the DB)
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)
LST_FILE = os.path.join(HISTORY_DIR, "last.csv")  # Legacy path, passed to functions but unused internally

# Tmp directory
TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)
WHO_FILE = os.path.join(TMP_DIR, "whopaid.txt")  # Who paid
ORD_FILE = os.path.join(TMP_DIR, "order.csv")  # The order
BAR_FILE = os.path.join(TMP_DIR, "bar.csv")  # What to ask at the bar
MAC_FILE = os.path.join(TMP_DIR, "machine.csv")  # What to put in the paying machine
DEB_FILE = os.path.join(TMP_DIR, "debts.csv")  # Debts per user

# Initialize database (idempotent: creates tables only if they don't exist)
init_db()
if current_debts_is_empty():
    init_current_debts_from_yaml(USERS_FILE)

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = "Poll"
if "users" not in st.session_state:
    st.session_state.users = load_users(USERS_FILE)

# Additional paraphernalia to get the sidebar to auto-collapse
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"  # page loads collapsed
if "menu" not in st.session_state:
    st.session_state.menu = "Poll ☕"
if "collapse_stage" not in st.session_state:
    st.session_state.collapse_stage = 0  # 0 = idle
if st.session_state.collapse_stage == 1:
    st.session_state.sidebar_state = "expanded"  # fake open state


def want_to_collapse():
    st.session_state.collapse_stage = 1


# Set name and icon to webpage
st.set_page_config(
    page_title="Café GTI",
    page_icon="☕",
    initial_sidebar_state=st.session_state.sidebar_state,
)


# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll ☕", "Current 💥", "Debts 💲", "History 📜", "Statistics 📊", "Morosos 👻"], key="menu", on_change=want_to_collapse)

# Sidebar auto-collapse paraphernalia
if st.session_state.collapse_stage == 1:
    time.sleep(0.05)  # let Phase 1 reach browser
    st.session_state.sidebar_state = "collapsed"
    st.session_state.collapse_stage = 2  # so we don’t loop forever
    st.rerun()
if st.session_state.collapse_stage == 2:
    st.session_state.collapse_stage = 0  # back to “idle”

match menu:
    # Poll view to create an order
    case "Poll ☕":
        poll(ORD_FILE, USERS_FILE, LST_FILE)

    # Current view to display the current order
    case "Current 💥":
        current(HISTORY_DIR, WHO_FILE, ORD_FILE, BAR_FILE, MAC_FILE, DEB_FILE, LST_FILE)

    # Debts view to check debts
    case "Debts 💲":
        debts(USERS_FILE, LST_FILE)

    # History view to check past summaries
    case "History 📜":
        history(HISTORY_DIR, WHO_FILE, ORD_FILE, BAR_FILE, MAC_FILE, DEB_FILE)

    # Statistics view to see analytics
    case "Statistics 📊":
        statistics(HISTORY_DIR, WHO_FILE, ORD_FILE, BAR_FILE, MAC_FILE, DEB_FILE, USERS_FILE)

    # Morosos view to see the stories of everyone
    case "Morosos 👻":
        morosos(LST_FILE)


if __name__ == "__main__":
    # Define the port you want your app to run on
    PORT = 8500

    # Check if Streamlit is already running on the specified port
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        s.close()
        print(f"Streamlit is already running on port {PORT}.")
    except (socket.error, ConnectionRefusedError):
        print(f"Launching Streamlit app on port {PORT}...")
        # Run Streamlit programmatically
        subprocess.run(
            ["streamlit", "run", __file__, "--server.port", str(PORT), "--server.baseUrlPath=/cafe", "--server.headless=false", "--browser.serverAddress=www.gti.ssr.upm.es"],
            check=True,
        )
