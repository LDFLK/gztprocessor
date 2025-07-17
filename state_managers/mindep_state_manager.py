# state_managers/mindep_state_manager.py

from state_managers.state_manager import AbstractStateManager
from db_connections.db_gov import get_connection
from pathlib import Path
import json

class MindepStateManager(AbstractStateManager):
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent
        state_dir = project_root / "state" / "mindep"
        super().__init__(state_dir)

    def export_state_snapshot(self, gazette_number: str, date_str: str):
        snapshot = {"ministers": []}

        try:
            with get_connection() as conn:
                cur = conn.cursor()

                cur.execute("SELECT id, name FROM ministry ORDER BY id ASC")
                ministries = cur.fetchall()

                for ministry_id, ministry_name in ministries:
                    cur.execute(
                        "SELECT name FROM department WHERE ministry_id = ? ORDER BY position ASC",
                        (ministry_id,),
                    )
                    departments = [row[0] for row in cur.fetchall()]
                    snapshot["ministers"].append({
                        "name": ministry_name,
                        "departments": departments
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
        ministries = state_data.get("ministers", [])

        if not ministries:
            raise ValueError(f"No ministries found in state file for {date_str}")

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM department")
            cur.execute("DELETE FROM ministry")

            for ministry in ministries:
                cur.execute("INSERT INTO ministry (name) VALUES (?)", (ministry["name"],))
                ministry_id = cur.lastrowid

                for pos, dept in enumerate(ministry["departments"], start=1):
                    cur.execute(
                        "INSERT INTO department (name, ministry_id, position) VALUES (?, ?, ?)",
                        (dept, ministry_id, pos),
                    )
            conn.commit()

        print(f"✅ Loaded state for {date_str} into the database.")

    def clear_db(self):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM department")
            cur.execute("DELETE FROM ministry")
            conn.commit()
        print(" Ministry and department tables cleared.")
