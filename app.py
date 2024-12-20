import os
import subprocess
import streamlit as st

from views import poll, current, history, debts, spotlight
from utils import load_users


# Local Directory Configuration
os.makedirs("tmp", exist_ok=True)
HISTORY_DIR = "history"
WHOPAID_FILE = "tmp/whopaid.txt"
ORDER_FILE = "tmp/current_order.csv"
BAR_FILE = "tmp/bar.csv"
MACHINE_FILE = "tmp/machine.csv"
DEBTS_FILE = "tmp/debts.csv"
USERS_FILE = "inputs/users.yaml"
BACKUP_FILE = "inputs/settleup_backup.csv"

# Set name and icon to webpage
st.set_page_config(
    page_title="Café GTI",
    page_icon="☕",
)

# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = 'Poll'
if "users" not in st.session_state:
    st.session_state.users = load_users(USERS_FILE)

# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll ☕", "Current 💥", "Debts 💲", "History 📜", "Spotlight 🎇"])
match menu:
    case "Poll ☕":
        # Poll view to create an order
        poll(ORDER_FILE)
    case "Current 💥":
        # Current view to display the current order
        current(HISTORY_DIR, WHOPAID_FILE, ORDER_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE, BACKUP_FILE)
    case "Debts 💲":
        # Debts view to check debts
        debts(HISTORY_DIR, USERS_FILE, DEBTS_FILE, BACKUP_FILE)
    case "History 📜":
        # History view to check past summaries
        history(HISTORY_DIR, WHOPAID_FILE, ORDER_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    case "Spotlight 🎇":
        spotlight()


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
        subprocess.run(["streamlit", "run", __file__, "--server.port", str(PORT)], check=True)
