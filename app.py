import os
import subprocess
import streamlit as st
from views import poll, current, history, debts, morosos
from utils import load_users, load_settleup, save_csv


# Inputs directory
USERS_FILE = "inputs/users.yaml"  # Users, initial debts, and description

# History directory
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)
LST_FILE = os.path.join(HISTORY_DIR, "last.csv")  # Last debts

# Tmp directory
TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)
WHO_FILE = os.path.join(TMP_DIR, "whopaid.txt")  # Who paid
ORD_FILE = os.path.join(TMP_DIR, "order.csv")  # The order
BAR_FILE = os.path.join(TMP_DIR, "bar.csv")  # What to ask at the bar
MAC_FILE = os.path.join(TMP_DIR, "machine.csv")  # What to put in the paying machine
DEB_FILE = os.path.join(TMP_DIR, "debts.csv")  # Debts per user

# Set name and icon to webpage
st.set_page_config(
    page_title="Café GTI",
    page_icon="☕",
)

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = "Poll"
if "users" not in st.session_state:
    st.session_state.users = load_users(USERS_FILE)
if not os.path.isfile(LST_FILE):
    save_csv(load_settleup(USERS_FILE), LST_FILE)

# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll ☕", "Current 💥", "Debts 💲", "History 📜", "Morosos 👻"])
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

    # Spotlight view to see the story of the person with larger debt
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
