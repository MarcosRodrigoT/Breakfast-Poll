import os
import pandas as pd
from datetime import datetime


def update_debts(users, history_dir, debts_file, whopaid='', price=0, backup_file=''):
    
    # Get the latest history debts
    historic_debts, history_dirs = get_last_debts(history_dir, users, backup_file, debt_update=True)

    # Load current debts from debts file
    current_debts = load_debts(debts_file, users, backup_file)
    current_debts = dict(zip(current_debts["Name"], current_debts["Debt"].astype(float)))

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
    debts_file_ = os.path.join(latest_history_dir, "debts.csv")
    historic_debts.to_csv(debts_file_, index=False)


def get_last_debts(history_dir, users, backup_file='', debt_update=False):
    debt_update_ = int(debt_update)
    
    # Get the latest history directory
    history_dirs = sorted(
        [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))],
        key=lambda x: pd.to_datetime(x, format="%Y-%m-%d_%H-%M-%S"),
        reverse=True,
    )
    
    # Get path to last debt
    if len(history_dirs) > debt_update_:
        history_aux = history_dirs[debt_update_] # 0 corresponds to the lastest (just created) file, read from the previous one for debt update only
        latest_history_dir = os.path.join(history_dir, history_aux)
        historic_debts_file = os.path.join(latest_history_dir, "debts.csv")
    else:
        historic_debts_file = ""
    
    # Load last debt
    historic_debts = load_debts(historic_debts_file, users, backup_file)
    return historic_debts, history_dirs


def load_debts(debts_file, users=[], backup_file=''):
    
    # Read csv if exists
    if os.path.exists(debts_file):
        debts = pd.read_csv(debts_file)
    else:
        
        # Read backup file if exists
        if os.path.exists(backup_file):
            debts = pd.read_csv(backup_file)
        
        # Else, return an empty debt dataframe
        else:
            debts = pd.DataFrame({"Name": users, "Debt": [0.0] * len(users)})
            debts["Debt"] = debts["Debt"].astype(float)
    return debts