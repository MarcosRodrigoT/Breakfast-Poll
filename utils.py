import pandas as pd
from datetime import datetime
import os


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
def save_current_selection_to_file(current_selections, selections_file):
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

    return timestamp
