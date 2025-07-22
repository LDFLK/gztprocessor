from abc import ABC, abstractmethod
from pathlib import Path
class AbstractStateManager(ABC):
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_connection(self): ...

    @abstractmethod
    def _get_state_from_db(self, cur, gazette_number: str, date_str: str) -> dict: ...

    @abstractmethod
    def get_gazette_numbers_for_date(self, cur, date_str: str) -> list[str]: ...

    @abstractmethod
    def export_state_snapshot(self, gazette_number: str, date_str: str): ...

    @abstractmethod
    def get_latest_state_info(self) -> tuple[str, str]: ...

    @abstractmethod
    def clear_db(self): ...

    def get_state_file_path(self, gazette_number: str, date_str: str) -> Path:
        filename = f"state_{gazette_number}_{date_str}.json"
        return self.state_dir / filename

    def get_latest_state(self) -> tuple[str, str, dict]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            gazette_number, date_str = self.get_latest_db_row(cur)
            state = self._get_state_from_db(cur, gazette_number, date_str)
            return gazette_number, date_str, state

    def get_state_by_date(self, date_str: str) -> dict | list[str]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            gazettes = self.get_gazette_numbers_for_date(cur, date_str)
            if not gazettes:
                raise FileNotFoundError(f"No state found for date {date_str}")
            if len(gazettes) == 1:
                gazette_number = gazettes[0]
                state = self._get_state_from_db(cur, gazette_number, date_str)
                return {"gazette_number": gazette_number, "state": state}
            return gazettes

    def load_state(self, gazette_number: str, date_str: str) -> dict:
        with self.get_connection() as conn:
            cur = conn.cursor()
            return self._get_state_from_db(cur, gazette_number, date_str)

    def clear_all_state_data(self):
        for f in self.state_dir.glob("state_*.json"):
            f.unlink()
        self.clear_db()