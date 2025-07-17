from db_connections.db_gov import get_connection
from collections import defaultdict
from state_managers.mindep_state_manager import MindepStateManager

mindep_state_manager = MindepStateManager()

def load_initial_state_to_db(gazette_number: str, date_str: str, ministries: list[dict]):
    """
    Load the first full structure into the database and save a state snapshot.
    Expects JSON format:
    {
      "ministries": [
        {
          "name": "Minister of X",
          "departments": ["Dept A", "Dept B"]
        }
      ]
    }
    Saves state to DB and also state/state_<date_str>.json
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()

            for ministry in ministries:
                cur.execute(
                    "INSERT INTO ministry (name) VALUES (?)",
                    (ministry["name"],),
                )
                ministry_id = cur.lastrowid

                position = 1  # reset for each ministry
                for dept in ministry["departments"]:
                    cur.execute(
                        "INSERT INTO department (name, ministry_id, position) VALUES (?, ?, ?)",
                        (dept, ministry_id, position),
                    )
                    position += 1

            conn.commit()
    except Exception as e:
        raise RuntimeError(f"Failed to insert initial state into database: {e}")

    print(f"Initial state inserted into database for {date_str}")

    # Export the inserted state back to a JSON file as a snapshot
    try:
        mindep_state_manager.export_state_snapshot(gazette_number, date_str)
    except Exception as e:
        raise RuntimeError(f"Failed to export state snapshot: {e}")


def apply_transactions_to_db(gazette_number: str, date_str: str, transactions: list[dict]):

    with get_connection() as conn:
        cur = conn.cursor()

        # Step 1: Load current structure from DB
        ministry_depts = defaultdict(
            list
        )  # ministry_name -> [department_name1, department_name2, ...]

        cur.execute(
            """
            SELECT m.name, d.name 
            FROM ministry m 
            JOIN department d ON m.id = d.ministry_id 
            ORDER BY m.id, d.position
        """
        )
        for ministry_name, dept_name in cur.fetchall():
            ministry_depts[ministry_name].append(dept_name)

        # Step 2: Apply transactions in memory
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

                # Remove from old ministry
                ministry_depts[from_min].remove(dept)

                # Insert into new ministry at correct position
                if pos is not None:
                    insert_at = pos - 1
                    if insert_at < 0:
                        insert_at = 0
                    ministry_depts[to_min].insert(insert_at, dept)
                else:
                    ministry_depts[to_min].append(dept)

            elif t == "ADD":
                to_min = tx["to_ministry"]
                pos = tx.get("position")

                # Avoid duplicates
                if dept in ministry_depts[to_min]:
                    continue

                if pos is not None:
                    insert_at = pos - 1
                    if insert_at < 0:
                        insert_at = 0
                    ministry_depts[to_min].insert(insert_at, dept)
                else:
                    ministry_depts[to_min].append(dept)

            elif t == "TERMINATE":
                from_min = tx["from_ministry"]
                if dept in ministry_depts[from_min]:
                    ministry_depts[from_min].remove(dept)

        # Step 3: Clear all departments
        cur.execute("DELETE FROM department")

        # Step 4: Re-insert departments with correct positions
        for ministry_name, departments in ministry_depts.items():
            # Get or create ministry
            cur.execute("SELECT id FROM ministry WHERE name = ?", (ministry_name,))
            row = cur.fetchone()
            if row:
                ministry_id = row[0]
            else:
                cur.execute("INSERT INTO ministry (name) VALUES (?)", (ministry_name,))
                ministry_id = cur.lastrowid

            for idx, dept_name in enumerate(departments, start=1):
                cur.execute(
                    "INSERT INTO department (name, ministry_id, position) VALUES (?, ?, ?)",
                    (dept_name, ministry_id, idx),
                )

        conn.commit()
        print("DB updated with new positions")

    # Step 5: Export state snapshot
    mindep_state_manager.export_state_snapshot(gazette_number,date_str)
    print(f"Exported state snapshot for {date_str}")
