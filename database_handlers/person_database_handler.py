# database_handlers/person_database_handler.py
from db_connections.db_person import get_connection
from state_managers.person_state_manager import PersonStateManager

person_state_manager = PersonStateManager()

def apply_transactions_to_db(gazette_number: str, date_str: str, transactions: dict):
    txs = transactions.get("transactions", transactions)

    with get_connection() as conn:
        cur = conn.cursor()

        print(f" Applying transactions for gazette {gazette_number} on {date_str}")

        # 1. Remove any existing records for this gazette_number/date
        cur.execute("SELECT id FROM person WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))
        person_ids = [r[0] for r in cur.fetchall()]
        if person_ids:
            cur.execute("DELETE FROM portfolio WHERE person_id IN ({})".format(",".join(["?"]*len(person_ids))), person_ids)
            cur.execute("DELETE FROM person WHERE gazette_number = ? AND date = ?", (gazette_number, date_str))

        # 2. Get the previous state (latest gazette_number/date before this one)
        try:
            prev_gazette, prev_date = person_state_manager.get_latest_state_info(cur, gazette_number, date_str)
            prev_state = person_state_manager._get_state_from_db(cur, prev_gazette, prev_date)
        except FileNotFoundError:
            prev_state = {"persons": []}

        # 3. Build new state in memory
        # Map: person_name -> {"person_name": ..., "portfolios": [...]}
        new_state = {}
        for person in prev_state["persons"]:
            new_state[person["person_name"]] = {
                "person_name": person["person_name"],
                "portfolios": [pf.copy() for pf in person["portfolios"]]
            }

        # Apply TERMINATEs
        for tx in txs.get("terminates", []):
            name = tx["name"]
            ministry = tx["ministry"]
            if name in new_state:
                new_state[name]["portfolios"] = [pf for pf in new_state[name]["portfolios"] if pf["name"] != ministry]
                # If no portfolios left, remove person
                if not new_state[name]["portfolios"]:
                    del new_state[name]

        # Apply MOVEs
        for tx in txs.get("moves", []):
            name = tx["name"]
            to_ministry = tx["to_ministry"]
            to_position = tx["to_position"]
            from_ministry = tx["from_ministry"]
            # Remove old portfolio
            if name in new_state:
                new_state[name]["portfolios"] = [pf for pf in new_state[name]["portfolios"] if pf["name"] != from_ministry]
            else:
                new_state[name] = {"person_name": name, "portfolios": []}
            # Add new portfolio if not already present
            if not any(pf["name"] == to_ministry and pf["position"] == to_position for pf in new_state[name]["portfolios"]):
                new_state[name]["portfolios"].append({"name": to_ministry, "position": to_position})

        # Apply ADDs
        for tx in txs.get("adds", []):
            name = tx["new_person"]
            ministry = tx["new_ministry"]
            position = tx["new_position"]
            if name not in new_state:
                new_state[name] = {"person_name": name, "portfolios": []}
            # Add new portfolio if not already present
            if not any(pf["name"] == ministry and pf["position"] == position for pf in new_state[name]["portfolios"]):
                new_state[name]["portfolios"].append({"name": ministry, "position": position})

        # Apply RENAMEs
        for tx in txs.get("renames", []):
            name = tx["name"]
            old_ministry = tx["old_ministry"]
            new_ministry = tx["new_ministry"]

            if name in new_state:
                portfolios = new_state[name]["portfolios"]
                found = False
                for pf in portfolios:
                    if pf["name"] == old_ministry:
                        pf["name"] = new_ministry 
                        found = True
                if not found:
                    print(f"⚠️ RENAME skipped: '{old_ministry}' not found under '{name}'")
            else:
                print(f"⚠️ RENAME skipped: person '{name}' not found in current state")


        # 4. Insert new state into person/portfolio with gazette_number/date
        for person in new_state.values():
            cur.execute(
                "INSERT INTO person (name, gazette_number, date) VALUES (?, ?, ?)",
                (person["person_name"], gazette_number, date_str)
            )
            person_id = cur.lastrowid
            for pf in person["portfolios"]:
                cur.execute(
                    "INSERT INTO portfolio (name, position, person_id, gazette_number, date) VALUES (?, ?, ?, ?, ?)",
                    (pf["name"], pf["position"], person_id, gazette_number, date_str)
                )

        conn.commit()
        print(f"Person-portfolio DB updated for {gazette_number} on {date_str}")

        # Save snapshot
        person_state_manager.export_state_snapshot(gazette_number, date_str)

