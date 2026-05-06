#!/usr/bin/env python3
"""
One-time migration: populate breakfast_poll.db from existing CSV history files.

Run from the project root:
    python migrate_to_db.py

Safe to run multiple times — already-migrated sessions are skipped.
"""

import os
import sys
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from utils.db_utils import init_db, get_db

HISTORY_DIR = PROJECT_ROOT / "history"
LST_FILE = HISTORY_DIR / "last.csv"


def parse_whopaid(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        line = f.readline().strip()
    # Format: "Name - Price"
    name, price = line.rsplit(" - ", 1)
    return name.strip(), float(price.strip())


def migrate_sessions(already_done):
    dirs = sorted(
        d.name for d in HISTORY_DIR.iterdir() if d.is_dir()
    )
    print(f"Found {len(dirs)} session directories ({len(already_done)} already in DB).")

    migrated = skipped = errors = 0

    for dirname in dirs:
        if dirname in already_done:
            skipped += 1
            continue

        dir_path = HISTORY_DIR / dirname
        try:
            paid_by, total_price = parse_whopaid(dir_path / "whopaid.txt")

            order_df = pd.read_csv(dir_path / "order.csv")
            if "Debt" not in order_df.columns:
                order_df["Debt"] = 0.0

            bar_df = pd.read_csv(dir_path / "bar.csv")
            machine_df = pd.read_csv(dir_path / "machine.csv")
            debts_df = pd.read_csv(dir_path / "debts.csv")

            with get_db() as conn:
                cursor = conn.execute(
                    "INSERT INTO sessions (timestamp, paid_by, total_price) VALUES (?, ?, ?)",
                    (dirname, paid_by, total_price),
                )
                sid = cursor.lastrowid

                for _, row in order_df.iterrows():
                    conn.execute(
                        "INSERT INTO orders (session_id, name, drink, food, individual_debt) VALUES (?, ?, ?, ?, ?)",
                        (sid, str(row["Name"]), str(row["Drinks"]), str(row["Food"]), float(row["Debt"])),
                    )
                for _, row in bar_df.iterrows():
                    conn.execute(
                        "INSERT INTO bar_items (session_id, item, amount) VALUES (?, ?, ?)",
                        (sid, str(row["Item"]), int(row["Amount"])),
                    )
                for _, row in machine_df.iterrows():
                    conn.execute(
                        "INSERT INTO machine_items (session_id, item, amount) VALUES (?, ?, ?)",
                        (sid, str(row["Item"]), int(row["Amount"])),
                    )
                for _, row in debts_df.iterrows():
                    conn.execute(
                        "INSERT INTO debt_snapshots (session_id, name, debt) VALUES (?, ?, ?)",
                        (sid, str(row["Name"]), float(row["Debt"])),
                    )

            migrated += 1
            if migrated % 50 == 0:
                print(f"  ... {migrated} sessions migrated so far")

        except Exception as e:
            errors += 1
            print(f"  ERROR in {dirname}: {e}")

    return migrated, skipped, errors


def migrate_current_debts():
    if not LST_FILE.exists():
        print("  last.csv not found — skipping current_debts migration.")
        return 0

    last_df = pd.read_csv(LST_FILE)
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM current_debts").fetchone()[0]
        if existing:
            print(f"  current_debts already has {existing} rows — skipping.")
            return existing

        for _, row in last_df.iterrows():
            conn.execute(
                "INSERT INTO current_debts (name, debt) VALUES (?, ?)",
                (str(row["Name"]), float(row["Debt"])),
            )
    print(f"  Migrated {len(last_df)} users from last.csv → current_debts.")
    return len(last_df)


def main():
    print("=== Breakfast-Poll → SQLite migration ===\n")

    print("Step 1: Initialising database schema...")
    init_db()
    print("  Done.\n")

    print("Step 2: Migrating session history...")
    with get_db() as conn:
        already_done = {row[0] for row in conn.execute("SELECT timestamp FROM sessions").fetchall()}

    migrated, skipped, errors = migrate_sessions(already_done)
    print(f"  Migrated: {migrated}  |  Skipped: {skipped}  |  Errors: {errors}\n")

    print("Step 3: Migrating current debts (last.csv)...")
    migrate_current_debts()

    print("\n=== Migration complete ===")
    if errors:
        print(f"  ⚠  {errors} session(s) failed — check output above.")
    else:
        print("  All sessions migrated successfully.")


if __name__ == "__main__":
    main()
