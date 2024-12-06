import os
import yaml
import logging
import pandas as pd
from datetime import datetime


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


# Load temporary selections from the local file
def load_current_selections(selections_file):
    if os.path.exists(selections_file):
        return pd.read_csv(selections_file)
    else:
        return pd.DataFrame(columns=["Name", "Drinks", "Food"])


# Save current user selections to the local CSV file without overwriting previous data
def save_current_selections(current_selections, selections_file):
    current_selections["Drinks"] = current_selections["Drinks"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    current_selections["Food"] = current_selections["Food"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    if os.path.exists(selections_file):
        existing_selections = pd.read_csv(selections_file)
        combined_selections = pd.concat([existing_selections, current_selections]).drop_duplicates()
    else:
        combined_selections = current_selections

    combined_selections.to_csv(selections_file, index=False)


# Load history from the local directory
def load_history(history_dir, selections_file, bar_file, machine_file, debts_file):
    history = []

    try:
        history_dirs = [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))]

        for directory in history_dirs:
            dir_path = os.path.join(history_dir, directory)

            selection_df = pd.read_csv(os.path.join(dir_path, selections_file.split("/")[-1]))
            bar_df = pd.read_csv(os.path.join(dir_path, bar_file.split("/")[-1]))
            machine_df = pd.read_csv(os.path.join(dir_path, machine_file.split("/")[-1]))
            debts_df = pd.read_csv(os.path.join(dir_path, debts_file.split("/")[-1]))

            # Format prices to show only 2 decimals
            debts_df["Spent"] = debts_df["Spent"].apply(lambda x: f"{x:.2f}")

            history.append(
                {
                    "Date": directory,
                    "Selection": selection_df,
                    "Bar": bar_df,
                    "Machine": machine_df,
                    "Debts": debts_df,
                }
            )
    except FileNotFoundError:
        history = []
    return history


# Save the current summary to a text file in the local history directory
def save_summary_to_history(history_dir, selections_file, bar_file, machine_file, debts_file):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_dir_ = os.path.join(history_dir, timestamp)

    os.makedirs(history_dir_, exist_ok=True)

    selection_file_ = os.path.join(history_dir_, selections_file.split("/")[-1])
    bar_file_ = os.path.join(history_dir_, bar_file.split("/")[-1])
    machine_file_ = os.path.join(history_dir_, machine_file.split("/")[-1])
    debts_file_ = os.path.join(history_dir_, debts_file.split("/")[-1])

    if os.path.exists(selections_file):
        aux = pd.read_csv(selections_file)
        aux.to_csv(selection_file_, index=False)
    if os.path.exists(bar_file):
        aux = pd.read_csv(bar_file)
        aux.to_csv(bar_file_, index=False)
    if os.path.exists(machine_file):
        aux = pd.read_csv(machine_file)
        aux.to_csv(machine_file_, index=False)
    if os.path.exists(debts_file):
        aux = pd.read_csv(debts_file)
        aux.to_csv(debts_file_, index=False)

    # Update settle.csv with the accumulated debts
    update_settle_up(history_dir, debts_file)

    return timestamp


def update_settle_up(history_dir, debts_file):
    # Get the latest history directory
    history_dirs = sorted(
        [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))],
        key=lambda x: pd.to_datetime(x, format="%Y-%m-%d_%H-%M-%S"),
        reverse=True,
    )

    users = [
        "Invitado",
        "Anna",
        "Carlos Cortés",
        "Carlos Cuevas",
        "Carlos Roberto",
        "Celia Ibáñez",
        "César Díaz",
        "Dani Berjón",
        "Dani Fuertes",
        "David",
        "Enmin Zhong",
        "Enol Ayo",
        "Francisco Morán",
        "Javier Usón",
        "Jesús Gutierrez",
        "Julián Cabrera",
        "Isa Rodriguez",
        "Leyre Encío",
        "Marcos Rodrigo",
        "Marta Goyena",
        "Marta Orduna",
        "Martina",
        "Matteo",
        "Miki",
        "Narciso García",
        "Pablo Pérez",
        "Victoria",
    ]

    # Load the latest settle.csv if it exists
    settle_data = None
    if len(history_dirs) > 1:
        latest_history_dir = os.path.join(history_dir, history_dirs[1])  # 0 would correspond to the lastest (just created) file, read from the previous one instead
        settle_file = os.path.join(latest_history_dir, "settle.csv")
        if os.path.exists(settle_file):
            settle_data = pd.read_csv(settle_file)
    if settle_data is None:
        settle_data = pd.DataFrame({"Name": users, "Debt": [0.0] * len(users)})

    # Ensure the "Debt" column is of type float
    settle_data["Debt"] = settle_data["Debt"].astype(float)

    # Load current debts from debts_file
    if os.path.exists(debts_file):
        current_debts = pd.read_csv(debts_file)
        current_debts.rename(columns={"Spent": "Debt"}, inplace=True)  # Align column name with settle.csv
        current_debts_dict = dict(zip(current_debts["Name"], current_debts["Debt"].astype(float)))
    else:
        current_debts_dict = {}

    # Update debts: Merge current debts into settle_data
    settle_data.set_index("Name", inplace=True)
    for user, debt in current_debts_dict.items():
        if user in settle_data.index:
            settle_data.at[user, "Debt"] += debt
        else:
            settle_data.loc[user] = debt  # Add new user with their debt
    settle_data.reset_index(inplace=True)

    # Save the updated settle.csv in the latest history directory
    if history_dirs:
        latest_history_dir = os.path.join(history_dir, history_dirs[0])
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        latest_history_dir = os.path.join(history_dir, timestamp)
        os.makedirs(latest_history_dir, exist_ok=True)

    settle_file = os.path.join(latest_history_dir, "settle.csv")
    settle_data.to_csv(settle_file, index=False)


def load_users(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["users"]
