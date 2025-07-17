# state_manager/base.py
from abc import ABC, abstractmethod
from pathlib import Path
import json

class AbstractStateManager(ABC):
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_file_path(self, gazette_number: str, date_str: str) -> Path:
        return self.state_dir / f"state_{gazette_number}_{date_str}.json"

    def get_latest_state_file(self) -> Path:
        state_files = list(self.state_dir.glob("state_*.json"))
        if not state_files:
            raise FileNotFoundError("No state files found.")
        state_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return state_files[0]
    
    def get_latest_state(self) -> tuple[str, str, dict]:
        """
        Return (gazette_number, date_str, state_dict) of the most recent saved state,
        based on file modification time.
        """
        path = self.get_latest_state_file()
        try:
            gazette_number, date_str = path.stem.replace("state_", "").split("_", 1)
        except ValueError:
            raise ValueError(f"Unexpected state file name format: {path.name}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            return gazette_number, date_str, state_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {path}: {e}")

    def get_latest_state_date(self) -> tuple[str, str]:
        latest = self.get_latest_state_file()
        gazette_number, date_str = latest.stem.replace("state_", "").split("_", 1)
        return gazette_number, date_str

    def get_state_by_date(self, date_str: str) -> dict | list[str]:
        pattern = f"state_*_{date_str}.json"
        matching_files = list(self.state_dir.glob(pattern))
        if not matching_files:
            raise FileNotFoundError(f"No state file found for {date_str}")
        if len(matching_files) == 1:
            path = matching_files[0]
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            gazette_number, _ = path.stem.replace("state_", "").split("_", 1)
            return {"gazette_number": gazette_number, "state": state}
        else:
            return [f.stem.replace("state_", "").split("_", 1)[0] for f in matching_files]

    def load_state(self, gazette_number: str, date_str: str) -> dict:
        path = self.get_state_file_path(gazette_number, date_str)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clear_all_state_data(self):
        for f in self.state_dir.glob("state_*.json"):
            f.unlink()
        self.clear_db()

    @abstractmethod
    def export_state_snapshot(self, gazette_number: str, date_str: str): ...
    
    @abstractmethod
    def load_state_to_db(self, gazette_number: str, date_str: str): ...
    
    @abstractmethod
    def clear_db(self): ...
