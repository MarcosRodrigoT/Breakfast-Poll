import os
import pandas as pd
from datetime import datetime


def update_debts(users, history_dir, debts_file, whopaid="", price=0):
    
    # Get the latest history directory
    history_dirs = sorted(
        [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))],
        key=lambda x: pd.to_datetime(x, format="%Y-%m-%d_%H-%M-%S"),
        reverse=True,
    )

    # Load the latest historic debts file (if any)
    historic_debts = None
    if len(history_dirs) > 1:
        latest_history_dir = os.path.join(history_dir, history_dirs[1])  # 0 corresponds to the lastest (just created) file, read from the previous one instead
        historic_debts_file = os.path.join(latest_history_dir, debts_file.split('/')[-1])
        if os.path.exists(historic_debts_file):
            historic_debts = pd.read_csv(historic_debts_file)
    if historic_debts is None:
        historic_debts = pd.DataFrame({"Name": users, "Debt": [0.0] * len(users)})

    # Ensure debt column is float
    historic_debts["Debt"] = historic_debts["Debt"].astype(float)

    # Load current debts from debts file
    if os.path.exists(debts_file):
        current_debts = pd.read_csv(debts_file)
        current_debts.rename(columns={"Spent": "Debt"}, inplace=True)
        current_debts = dict(zip(current_debts["Name"], current_debts["Debt"].astype(float)))
    else:
        current_debts = {}

    # Update debts: Merge current debts with historic debts
    historic_debts.set_index("Name", inplace=True)
    for user, debt in current_debts.items():
        if user == whopaid:
            debt -= price
        if user in historic_debts.index:
            historic_debts.at[user, "Debt"] += debt
        else:
            historic_debts.loc[user] = debt  # Add new user with their debt
    historic_debts.reset_index(inplace=True)

    # Save the new debts in the latest history directory
    if len(history_dirs) > 1:
        latest_history_dir = os.path.join(history_dir, history_dirs[0])
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        latest_history_dir = os.path.join(history_dir, timestamp)
        os.makedirs(latest_history_dir, exist_ok=True)
    debts_file_ = os.path.join(latest_history_dir, debts_file.split('/')[-1])
    historic_debts.to_csv(debts_file_, index=False)
