from state_managers.state_manager import AbstractStateManager
from db_connections.db_person import get_connection
from pathlib import Path
import json

class PersonStateManager(AbstractStateManager):
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent
        state_dir = project_root / "state" / "person"
        super().__init__(state_dir)

    def export_state_snapshot(self, gazette_number: str, date_str: str):
        snapshot = {"persons": []}

        try:
            with get_connection() as conn:
                cur = conn.cursor()

                # Get all persons
                cur.execute("SELECT id, name FROM person ORDER BY id ASC")
                persons = cur.fetchall()

                for person_id, person_name in persons:
                    cur.execute(
                        """
                        SELECT name, position
                        FROM portfolio
                        WHERE person_id = ?
                        ORDER BY id ASC
                        """,
                        (person_id,),
                    )
                    portfolios = [
                        {"name": row[0], "position": row[1]}
                        for row in cur.fetchall()
                    ]

                    snapshot["persons"].append({
                        "person_name": person_name,
                        "portfolios": portfolios
                    })

        except Exception as e:
            raise RuntimeError(f"Failed to query state data: {e}")

        try:
            state_path = self.get_state_file_path(gazette_number, date_str)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            print(f"✅ State snapshot exported to {state_path}")
        except IOError as e:
            raise IOError(f"Failed to write state snapshot to {state_path}: {e}")

    def load_state_to_db(self, gazette_number: str, date_str: str):
        state_data = self.load_state(gazette_number, date_str)
        persons = state_data.get("persons", [])

        if not persons:
            raise ValueError(f"No persons found in state file for {date_str}")

        with get_connection() as conn:
            cur = conn.cursor()

            # Clear existing data
            cur.execute("DELETE FROM portfolio")
            cur.execute("DELETE FROM person")

            for person in persons:
                person_name = person["person_name"]
                cur.execute("INSERT INTO person (name) VALUES (?)", (person_name,))
                person_id = cur.lastrowid

                for pf in person["portfolios"]:
                    cur.execute(
                        "INSERT INTO portfolio (name, position, person_id) VALUES (?, ?, ?)",
                        (pf["name"], pf["position"], person_id),
                    )

            conn.commit()

        print(f"✅ Loaded state for {date_str} into the database.")

    def clear_db(self):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM portfolio")
            cur.execute("DELETE FROM person")
            conn.commit()
        print("✅ Person and portfolio tables cleared.")
