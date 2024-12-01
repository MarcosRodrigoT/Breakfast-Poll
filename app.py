import streamlit as st
import os
import subprocess
from utils import load_current_selections, load_history
from views import poll, current, history, settle


# Local Directory Configuration
os.makedirs("tmp", exist_ok=True)
HISTORY_DIR = "history"
SELECTION_FILE = "tmp/current_selections.csv"
BAR_FILE = "tmp/bar.csv"
MACHINE_FILE = "tmp/machine.csv"
DEBTS_FILE = "tmp/debts.csv"


# Initialize all required session state variables
if "users" not in st.session_state:
    st.session_state.users = []
if "current_selections" not in st.session_state:
    st.session_state.current_selections = []
if "step" not in st.session_state:
    st.session_state.step = 1
if "history" not in st.session_state:
    st.session_state.history = load_history(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    st.session_state.current_selections = load_current_selections(SELECTION_FILE).to_dict(orient="records")


# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll", "Current", "Settle", "History"])

match menu:
    case "Poll":
        # Poll view with four consecutive steps
        poll(SELECTION_FILE)
    case "Current":
        # "Current" view to display the current summary of all users' selections and generate ticket
        current(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)
    case "Settle":
        # Check settle up results and bar plot with debts
        settle(HISTORY_DIR, DEBTS_FILE)
    case "History":
        # History view to check past summaries
        history(HISTORY_DIR, SELECTION_FILE, BAR_FILE, MACHINE_FILE, DEBTS_FILE)


if __name__ == "__main__":
    # Define the port you want your app to run on
    PORT = 8500  # Replace with your preferred port number

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
