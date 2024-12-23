import os
import logging
from datetime import datetime

from utils.data_utils import load_whopaid, save_whopaid, load_csv, save_csv


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
def load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, last_file):
    
    # Load history directories
    history_dirs = [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))]
    
    # For each directory, get data
    history = []
    for directory in history_dirs:
        dir_path = os.path.join(history_dir, directory)

        # Load data
        whopaid = load_whopaid(os.path.join(dir_path, whopaid_file.split("/")[-1]))
        order_df = load_csv(os.path.join(dir_path, order_file.split("/")[-1]))
        bar_df = load_csv(os.path.join(dir_path, bar_file.split("/")[-1]))
        machine_df = load_csv(os.path.join(dir_path, machine_file.split("/")[-1]))
        debts_df = load_csv(os.path.join(dir_path, debts_file.split("/")[-1]))
        last_df = load_csv(os.path.join(dir_path, last_file.split("/")[-1]))

        # Format prices to show only 2 decimals
        debts_df["Debt"] = debts_df["Debt"].apply(lambda x: f"{x:.2f}")
        last_df["Debt"] = last_df["Debt"].apply(lambda x: f"{x:.2f}")

        # Save data
        history.append(
            {
                "Date": directory,
                "Whopaid": whopaid,
                "Order": order_df,
                "Bar": bar_df,
                "Machine": machine_df,
                "Debts": debts_df,
                "Last": last_df,
            }
        )
    return history


# Save the current summary to a text file in the local history directory
def save_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, last_file):
    
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
    last_file_ = os.path.join(history_dir_, last_file.split("/")[-1])

    # Move tmp files to history
    if os.path.exists(order_file):
        whopaid, price = load_whopaid(whopaid_file)
        save_whopaid(whopaid_file_, whopaid, price)
    if os.path.exists(order_file):
        save_csv(load_csv(order_file), order_file_)
    if os.path.exists(bar_file):
        save_csv(load_csv(bar_file), bar_file_)
    if os.path.exists(machine_file):
        save_csv(load_csv(machine_file), machine_file_)
    if os.path.exists(debts_file):
        save_csv(load_csv(debts_file), debts_file_)

    # Update accumulated debts (and move it to history)
    update_debts(whopaid_file, debts_file, last_file)
    if os.path.exists(last_file):
        save_csv(load_csv(last_file), last_file_)
    
    # Remove tmp data
    os.remove(whopaid_file)
    os.remove(order_file)
    os.remove(bar_file)
    os.remove(machine_file)
    os.remove(debts_file)

    return timestamp


def update_debts(whopaid_file, debts_file, last_file):
    
    # Load who paid
    whopaid, price = load_whopaid(whopaid_file)
    
    # Get latest debts
    last_debts = load_csv(last_file)
    last_debts.set_index("Name", inplace=True)

    # Load current debts from debts file
    curr_debts = load_csv(debts_file)
    curr_debts = dict(zip(curr_debts["Name"], curr_debts["Debt"].astype(float)))

    # Update debts: Merge current debts with historic debts
    for user, debt in curr_debts.items():
        if user == whopaid:
            debt -= price
        if user in last_debts.index:
            last_debts.at[user, "Debt"] += debt
        else:
            last_debts.loc[user] = debt
    last_debts.reset_index(inplace=True)

    # Save the new debts as last debts
    save_csv(last_debts, last_file)
