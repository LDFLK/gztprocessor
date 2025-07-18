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

    def get_connection(self):
        return get_connection()

    def get_latest_db_row(self, cur):
        cur.execute("SELECT gazette_number, date FROM ministry ORDER BY date DESC, gazette_number DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise FileNotFoundError("No state found in ministry DB.")
        return row

    def get_gazette_numbers_for_date(self, cur, date_str: str) -> list[str]:
        cur.execute("SELECT gazette_number FROM ministry WHERE date = ? GROUP BY gazette_number", (date_str,))
        return [row[0] for row in cur.fetchall()]

    def _get_state_from_db(self, cur, gazette_number: str, date_str: str) -> dict:
        snapshot = {"ministers": []}
        cur.execute("SELECT id, name FROM ministry WHERE gazette_number = ? AND date = ? ORDER BY id ASC", (gazette_number, date_str))
        for ministry_id, ministry_name in cur.fetchall():
            cur.execute(
                "SELECT name FROM department WHERE ministry_id = ? AND gazette_number = ? AND date = ? ORDER BY position ASC",
                (ministry_id, gazette_number, date_str),
            )
            departments = [row[0] for row in cur.fetchall()]
            snapshot["ministers"].append({
                "name": ministry_name,
                "departments": departments
            })
        return snapshot

    def export_state_snapshot(self, gazette_number: str, date_str: str):
        state = self._get_state_from_db(self.get_connection().cursor(), gazette_number, date_str)
        state_path = self.get_state_file_path(gazette_number, date_str)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"✅ Mindep snapshot exported to {state_path}")

    def clear_db(self):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM department")
            cur.execute("DELETE FROM ministry")
            conn.commit()
        print("🧹 Ministry and department tables cleared.")
