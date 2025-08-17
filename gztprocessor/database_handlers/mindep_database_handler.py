from gztprocessor.db_connections.db_gov import get_connection
from collections import defaultdict
from gztprocessor.state_managers.mindep_state_manager import MindepStateManager

mindep_state_manager = MindepStateManager()

def load_initial_state_to_db(gazette_number: str, date_str: str, ministries: list[dict]):
    with get_connection() as conn:
        cur = conn.cursor()

        # 1. Delete all ministries and departments for the incoming gazette_number and date_str
        cur.execute("SELECT id FROM ministry WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))
        ministry_ids = [r[0] for r in cur.fetchall()]
        if ministry_ids:
            cur.execute("DELETE FROM department WHERE ministry_id IN ({})".format(",".join(["?"]*len(ministry_ids))), ministry_ids)
            cur.execute("DELETE FROM ministry WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))

        # 2. Insert the new initial state
        for ministry in ministries:
            cur.execute(
                "INSERT INTO ministry (name, gazette_number, date) VALUES (?, ?, ?)",
                (ministry["name"], gazette_number, date_str)
            )
            ministry_id = cur.lastrowid
            position = 1
            for dept in ministry["departments"]:
                dept = dept["name"]
                cur.execute(
                    "INSERT INTO department (name, ministry_id, position, gazette_number, date) VALUES (?, ?, ?, ?, ?)",
                    (dept, ministry_id, position, gazette_number, date_str)
                )
                position += 1

        conn.commit()

    mindep_state_manager.export_state_snapshot(gazette_number, date_str)
    print(f"Initial state replaced for gazette {gazette_number} on {date_str}.")


def apply_transactions_to_db(gazette_number: str, date_str: str, transactions: dict):
    if isinstance(transactions, dict) and "transactions" in transactions:
        transactions = transactions["transactions"]
    if isinstance(transactions, dict):
        transactions = (
            transactions.get("moves", []) +
            transactions.get("adds", []) +
            transactions.get("terminates", [])
        )

    # Filter out any invalid transactions with empty departments or ministries
    transactions = [
        tx for tx in transactions
        if tx.get("type") and tx.get("department") and (
            tx["type"] != "ADD" or tx.get("to_ministry")
        ) and (
            tx["type"] != "MOVE" or (tx.get("to_ministry") and tx.get("from_ministry"))
        ) and (
            tx["type"] != "TERMINATE" or tx.get("from_ministry")
        )
    ]

    with get_connection() as conn:
        cur = conn.cursor()

        # 1. Get the latest gazette_number and date in the DB
        cur.execute("SELECT gazette_number, date FROM ministry ORDER BY date DESC, gazette_number DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            latest_gazette, latest_date = row
        else:
            # No data yet, return
            return

        # 2. Load the latest state into memory
        ministry_depts = defaultdict(list)
        cur.execute(
            """
            SELECT m.name, d.name
            FROM ministry m
            JOIN department d ON m.id = d.ministry_id
            WHERE m.gazette_number = ? AND m.date = ? AND d.gazette_number = ? AND d.date = ?
            ORDER BY m.id, d.position
            """,
            (latest_gazette, latest_date, latest_gazette, latest_date)
        )
        for ministry_name, dept_name in cur.fetchall():
            if ministry_name and dept_name:
                ministry_depts[ministry_name].append(dept_name)

        # 3. Apply transactions in memory
        for tx in transactions:
            t = tx["type"]
            dept = tx["department"]

            if t == "MOVE":
                from_min = tx["from_ministry"]
                to_min = tx["to_ministry"]
                pos = tx.get("position")
                if dept not in ministry_depts[from_min]:
                    print(f"⚠️ {dept} not found in {from_min}")
                    continue
                ministry_depts[from_min].remove(dept)
                if pos is not None:
                    insert_at = max(pos - 1, 0)
                    ministry_depts[to_min].insert(insert_at, dept)
                else:
                    ministry_depts[to_min].append(dept)

            elif t == "ADD":
                to_min = tx["to_ministry"]
                pos = tx.get("position")
                if dept in ministry_depts[to_min]:
                    continue
                if pos is not None:
                    insert_at = max(pos - 1, 0)
                    ministry_depts[to_min].insert(insert_at, dept)
                else:
                    ministry_depts[to_min].append(dept)

            elif t == "TERMINATE":
                from_min = tx["from_ministry"]
                if dept in ministry_depts[from_min]:
                    ministry_depts[from_min].remove(dept)

        # 4. Delete all ministries and departments for the incoming gazette_number and date_str
        cur.execute("SELECT id FROM ministry WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))
        ministry_ids = [r[0] for r in cur.fetchall()]
        if ministry_ids:
            cur.execute("DELETE FROM department WHERE ministry_id IN ({})".format(",".join(["?"]*len(ministry_ids))), ministry_ids)
            cur.execute("DELETE FROM ministry WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))

        # 5. Insert the new state
        ministry_id_map = {}
        for ministry_name, departments in ministry_depts.items():
            if not ministry_name or not departments:
                continue  # skip empty ministries
            cur.execute(
                "INSERT INTO ministry (name, gazette_number, date) VALUES (?, ?, ?)",
                (ministry_name, gazette_number, date_str)
            )
            ministry_id = cur.lastrowid
            ministry_id_map[ministry_name] = ministry_id
            for idx, dept_name in enumerate(departments, start=1):
                cur.execute(
                    "INSERT INTO department (name, ministry_id, position, gazette_number, date) VALUES (?, ?, ?, ?, ?)",
                    (dept_name, ministry_id, idx, gazette_number, date_str)
                )

        conn.commit()
        print("DB updated with new positions (versioned, no deletes)")

    mindep_state_manager.export_state_snapshot(gazette_number, date_str)
    print(f"Exported state snapshot for {date_str}")

