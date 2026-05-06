import os
import logging
import pandas as pd
from datetime import datetime
from utils.data_utils import load_whopaid, load_csv
from utils.db_utils import (
    load_all_sessions_from_db,
    save_session_to_db,
    update_current_debts_after_session,
    load_current_debts,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def format_date(date_str):
    original_format = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
    return original_format.strftime("%B %d, %Y - %H:%M:%S")


def load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    history = load_all_sessions_from_db()
    for record in history:
        record["Debts"]["Debt"] = record["Debts"]["Debt"].apply(lambda x: f"{x:.2f}")
    return history


def save_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, last_file):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    whopaid, price = load_whopaid(whopaid_file)
    order_df = load_csv(order_file)
    session_debts_df = load_csv(debts_file)
    bar_df = load_csv(bar_file)
    machine_df = load_csv(machine_file)

    combined_order = pd.merge(order_df, session_debts_df, on="Name", how="inner")

    session_debts_dict = dict(zip(session_debts_df["Name"], session_debts_df["Debt"].astype(float)))
    update_current_debts_after_session(whopaid, price, session_debts_dict)

    debt_snapshot = load_current_debts()
    save_session_to_db(timestamp, whopaid, price, combined_order, bar_df, machine_df, debt_snapshot)

    for f in [whopaid_file, order_file, bar_file, machine_file, debts_file]:
        if os.path.exists(f):
            os.remove(f)

    return timestamp


def update_debts(whopaid_file, debts_file, last_file):
    whopaid, price = load_whopaid(whopaid_file)
    curr_debts_df = load_csv(debts_file)
    session_debts_dict = dict(zip(curr_debts_df["Name"], curr_debts_df["Debt"].astype(float)))
    update_current_debts_after_session(whopaid, price, session_debts_dict)
