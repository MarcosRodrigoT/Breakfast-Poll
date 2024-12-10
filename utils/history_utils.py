import os
import logging
import pandas as pd
from datetime import datetime

from utils.debts_utils import update_debts
from utils.order_utils import load_whopaid, save_whopaid


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output to stdout (visible in journalctl)
    ],
)


# Helper function to format the date
def format_date(date_str):
    original_format = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")  # Convert string to datetime object
    formatted_date = original_format.strftime("%B %d, %Y - %H:%M:%S")  # Format to "November 29, 2024 - 15:50:34"
    return formatted_date


# Load history from the local directory
def load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    
    # Load history directories
    history_dirs = [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))]
    
    # For each directory, get data
    history = []
    for directory in history_dirs:
        dir_path = os.path.join(history_dir, directory)

        # Load data
        whopaid = load_whopaid(os.path.join(dir_path, whopaid_file.split("/")[-1]))
        order_df = pd.read_csv(os.path.join(dir_path, order_file.split("/")[-1]))
        bar_df = pd.read_csv(os.path.join(dir_path, bar_file.split("/")[-1]))
        machine_df = pd.read_csv(os.path.join(dir_path, machine_file.split("/")[-1]))
        debts_df = pd.read_csv(os.path.join(dir_path, debts_file.split("/")[-1]))

        # Format prices to show only 2 decimals
        debts_df["Debt"] = debts_df["Debt"].apply(lambda x: f"{x:.2f}")

        # Save data
        history.append(
            {
                "Date": directory,
                "Whopaid": whopaid,
                "Order": order_df,
                "Bar": bar_df,
                "Machine": machine_df,
                "Debts": debts_df,
            }
        )
    return history


# Save the current summary to a text file in the local history directory
def save_history(users, history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, backup_file=''):
    whopaid, price = "", 0
    
    # Create directory based on timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_dir_ = os.path.join(history_dir, timestamp)
    os.makedirs(history_dir_, exist_ok=True)

    # Get path to each file on tmp
    whopaid_file_ = os.path.join(history_dir_, whopaid_file.split("/")[-1])
    order_file_ = os.path.join(history_dir_, order_file.split("/")[-1])
    bar_file_ = os.path.join(history_dir_, bar_file.split("/")[-1])
    machine_file_ = os.path.join(history_dir_, machine_file.split("/")[-1])
    debts_file_ = os.path.join(history_dir_, debts_file.split("/")[-1])

    # Move tmp files to history
    if os.path.exists(order_file):
        whopaid, price = load_whopaid(whopaid_file)
        save_whopaid(whopaid_file_, whopaid, price)
    if os.path.exists(order_file):
        aux = pd.read_csv(order_file)
        aux.to_csv(order_file_, index=False)
    if os.path.exists(bar_file):
        aux = pd.read_csv(bar_file)
        aux.to_csv(bar_file_, index=False)
    if os.path.exists(machine_file):
        aux = pd.read_csv(machine_file)
        aux.to_csv(machine_file_, index=False)
    if os.path.exists(debts_file):
        aux = pd.read_csv(debts_file)
        aux.to_csv(debts_file_, index=False)

    # Update accumulated debts
    update_debts(users, history_dir, debts_file, whopaid, price, backup_file)
    
    # Remove tmp data
    os.remove(whopaid_file)
    os.remove(order_file)
    os.remove(bar_file)
    os.remove(machine_file)
    os.remove(debts_file)

    return timestamp