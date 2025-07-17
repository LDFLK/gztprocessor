# database_handlers/person_database_handler.py
from db_connections.db_person import get_connection
from state_managers.person_state_manager import PersonStateManager

person_state_manager = PersonStateManager()

def apply_transactions_to_db(gazette_number: str, date_str: str, transactions: dict):
    from collections import defaultdict
    txs = transactions.get("transactions", transactions)

    with get_connection() as conn:
        cur = conn.cursor()

        print(f" Applying transactions for gazette {gazette_number} on {date_str}")

        # MOVEs
        for tx in txs.get("moves", []):
            name = tx["name"]
            to_ministry = tx["to_ministry"]
            to_position = tx["to_position"]
            from_ministry = tx["from_ministry"]

            cur.execute("SELECT id FROM person WHERE name = ?", (name,))
            row = cur.fetchone()
            if row:
                person_id = row[0]
            else:
                cur.execute("INSERT INTO person (name) VALUES (?)", (name,))
                person_id = cur.lastrowid

            # Remove old portfolio
            cur.execute("DELETE FROM portfolio WHERE name = ? AND person_id = ?", (from_ministry, person_id))

            # Check for existing identical portfolio
            cur.execute(
                "SELECT 1 FROM portfolio WHERE name = ? AND position = ? AND person_id = ?",
                (to_ministry, to_position, person_id)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO portfolio (name, position, person_id) VALUES (?, ?, ?)",
                    (to_ministry, to_position, person_id)
                )

        # ADDs
        for tx in txs.get("adds", []):
            name = tx["new_person"]
            ministry = tx["new_ministry"]
            position = tx["new_position"]

            cur.execute("SELECT id FROM person WHERE name = ?", (name,))
            row = cur.fetchone()
            if row:
                person_id = row[0]
            else:
                cur.execute("INSERT INTO person (name) VALUES (?)", (name,))
                person_id = cur.lastrowid

            # Check for existing identical portfolio
            cur.execute(
                "SELECT 1 FROM portfolio WHERE name = ? AND position = ? AND person_id = ?",
                (ministry, position, person_id)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO portfolio (name, position, person_id) VALUES (?, ?, ?)",
                    (ministry, position, person_id)
                )

        # TERMINATEs
        for tx in txs.get("terminates", []):
            name = tx["name"]
            ministry = tx["ministry"]

            cur.execute("SELECT id FROM person WHERE name = ?", (name,))
            row = cur.fetchone()
            if row:
                person_id = row[0]
                cur.execute(
                    "DELETE FROM portfolio WHERE name = ? AND person_id = ?",
                    (ministry, person_id)
                )
            else:
                print(f"⚠️ Person not found for TERMINATE: {name}")

        conn.commit()
        print(f"Person-portfolio DB updated for {gazette_number} on {date_str}")

        # Save snapshot
        person_state_manager.export_state_snapshot(gazette_number, date_str)

