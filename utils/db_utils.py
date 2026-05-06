import os
import sqlite3
import pandas as pd
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "breakfast_poll.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    UNIQUE NOT NULL,
                paid_by     TEXT    NOT NULL,
                total_price REAL    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                name            TEXT    NOT NULL,
                drink           TEXT    NOT NULL,
                food            TEXT    NOT NULL,
                individual_debt REAL    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bar_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                item       TEXT    NOT NULL,
                amount     INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS machine_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                item       TEXT    NOT NULL,
                amount     INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS debt_snapshots (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                name       TEXT    NOT NULL,
                debt       REAL    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS current_debts (
                name TEXT PRIMARY KEY,
                debt REAL NOT NULL DEFAULT 0.0
            );
        """)


def current_debts_is_empty():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM current_debts").fetchone()[0]
    return count == 0


def init_current_debts_from_yaml(yaml_file):
    import yaml
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    with get_db() as conn:
        for name in data:
            conn.execute(
                "INSERT OR IGNORE INTO current_debts (name, debt) VALUES (?, 0.0)",
                (str(name),),
            )


def load_current_debts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name, debt FROM current_debts ORDER BY name"
        ).fetchall()
    return pd.DataFrame([(r["name"], r["debt"]) for r in rows], columns=["Name", "Debt"])


def add_user_to_current_debts(name, initial_debt=0.0):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT name FROM current_debts WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO current_debts (name, debt) VALUES (?, ?)",
            (name, initial_debt),
        )
    return True


def update_current_debts_after_session(paid_by, total_price, session_debts_dict):
    """Accumulate per-session individual debts into the running current_debts table."""
    with get_db() as conn:
        for user, debt in session_debts_dict.items():
            adjusted = debt - total_price if user == paid_by else debt
            existing = conn.execute(
                "SELECT debt FROM current_debts WHERE name = ?", (user,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE current_debts SET debt = debt + ? WHERE name = ?",
                    (adjusted, user),
                )
            else:
                conn.execute(
                    "INSERT INTO current_debts (name, debt) VALUES (?, ?)",
                    (user, adjusted),
                )


def save_session_to_db(timestamp, paid_by, total_price, order_df, bar_df, machine_df, debt_snapshot_df):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (timestamp, paid_by, total_price) VALUES (?, ?, ?)",
            (timestamp, paid_by, total_price),
        )
        session_id = cursor.lastrowid

        for _, row in order_df.iterrows():
            conn.execute(
                "INSERT INTO orders (session_id, name, drink, food, individual_debt) VALUES (?, ?, ?, ?, ?)",
                (session_id, str(row["Name"]), str(row["Drinks"]), str(row["Food"]), float(row["Debt"])),
            )
        for _, row in bar_df.iterrows():
            conn.execute(
                "INSERT INTO bar_items (session_id, item, amount) VALUES (?, ?, ?)",
                (session_id, str(row["Item"]), int(row["Amount"])),
            )
        for _, row in machine_df.iterrows():
            conn.execute(
                "INSERT INTO machine_items (session_id, item, amount) VALUES (?, ?, ?)",
                (session_id, str(row["Item"]), int(row["Amount"])),
            )
        for _, row in debt_snapshot_df.iterrows():
            conn.execute(
                "INSERT INTO debt_snapshots (session_id, name, debt) VALUES (?, ?, ?)",
                (session_id, str(row["Name"]), float(row["Debt"])),
            )


def count_sessions():
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]


def load_sessions_page(offset, limit):
    """Load `limit` sessions newest-first starting at `offset`, with all details."""
    with get_db() as conn:
        sessions = conn.execute(
            "SELECT id, timestamp, paid_by, total_price FROM sessions"
            " ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()

        result = []
        for s in sessions:
            sid = s["id"]
            order_rows = conn.execute(
                "SELECT name, drink, food, individual_debt FROM orders WHERE session_id = ?", (sid,)
            ).fetchall()
            bar_rows = conn.execute(
                "SELECT item, amount FROM bar_items WHERE session_id = ?", (sid,)
            ).fetchall()
            machine_rows = conn.execute(
                "SELECT item, amount FROM machine_items WHERE session_id = ?", (sid,)
            ).fetchall()
            debt_rows = conn.execute(
                "SELECT name, debt FROM debt_snapshots WHERE session_id = ?", (sid,)
            ).fetchall()

            result.append({
                "Date": s["timestamp"],
                "Whopaid": (s["paid_by"], s["total_price"]),
                "Order": pd.DataFrame(
                    [(r["name"], r["drink"], r["food"], r["individual_debt"]) for r in order_rows],
                    columns=["Name", "Drinks", "Food", "Debt"],
                ) if order_rows else pd.DataFrame(columns=["Name", "Drinks", "Food", "Debt"]),
                "Bar": pd.DataFrame(
                    [(r["item"], r["amount"]) for r in bar_rows],
                    columns=["Item", "Amount"],
                ) if bar_rows else pd.DataFrame(columns=["Item", "Amount"]),
                "Machine": pd.DataFrame(
                    [(r["item"], r["amount"]) for r in machine_rows],
                    columns=["Item", "Amount"],
                ) if machine_rows else pd.DataFrame(columns=["Item", "Amount"]),
                "Debts": pd.DataFrame(
                    [(r["name"], r["debt"]) for r in debt_rows],
                    columns=["Name", "Debt"],
                ) if debt_rows else pd.DataFrame(columns=["Name", "Debt"]),
            })

    return result


def load_all_sessions_from_db():
    with get_db() as conn:
        sessions = conn.execute(
            "SELECT id, timestamp, paid_by, total_price FROM sessions ORDER BY timestamp"
        ).fetchall()

        result = []
        for s in sessions:
            sid = s["id"]

            order_rows = conn.execute(
                "SELECT name, drink, food, individual_debt FROM orders WHERE session_id = ?", (sid,)
            ).fetchall()
            bar_rows = conn.execute(
                "SELECT item, amount FROM bar_items WHERE session_id = ?", (sid,)
            ).fetchall()
            machine_rows = conn.execute(
                "SELECT item, amount FROM machine_items WHERE session_id = ?", (sid,)
            ).fetchall()
            debt_rows = conn.execute(
                "SELECT name, debt FROM debt_snapshots WHERE session_id = ?", (sid,)
            ).fetchall()

            result.append({
                "Date": s["timestamp"],
                "Whopaid": (s["paid_by"], s["total_price"]),
                "Order": pd.DataFrame(
                    [(r["name"], r["drink"], r["food"], r["individual_debt"]) for r in order_rows],
                    columns=["Name", "Drinks", "Food", "Debt"],
                ) if order_rows else pd.DataFrame(columns=["Name", "Drinks", "Food", "Debt"]),
                "Bar": pd.DataFrame(
                    [(r["item"], r["amount"]) for r in bar_rows],
                    columns=["Item", "Amount"],
                ) if bar_rows else pd.DataFrame(columns=["Item", "Amount"]),
                "Machine": pd.DataFrame(
                    [(r["item"], r["amount"]) for r in machine_rows],
                    columns=["Item", "Amount"],
                ) if machine_rows else pd.DataFrame(columns=["Item", "Amount"]),
                "Debts": pd.DataFrame(
                    [(r["name"], r["debt"]) for r in debt_rows],
                    columns=["Name", "Debt"],
                ) if debt_rows else pd.DataFrame(columns=["Name", "Debt"]),
            })

    return result
