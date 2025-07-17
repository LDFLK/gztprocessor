import json
from pathlib import Path

MINDEP_INPUT_DIR = Path(__file__).resolve().parent / "input" / "mindep"
PERSON_INPUT_DIR = Path(__file__).resolve().parent / "input" / "person"

def load_mindep_gazette_data_from_JSON(gazette_number: str, date_str: str) -> dict:
    """
    Load a gazette JSON file using gazette number and date.
    Expected file names:
    - ministry-initial-<gazette_number>_E_<date_str>.json
    - ministry-amendment-<gazette_number>_E_<date_str>.json

    Example:
    - ministry-initial-2289-43_E_2022-07-22.json
    - ministry-amendment-2297-78_E_2022-09-16.json

    Note: date_str passed with hyphens ('YYYY-MM-DD') will be
    converted to underscores to match filenames.
    """

    # Convert hyphens to underscores so "2022-07-22" matches "2022_07_22"
    normalized_date_str = date_str.replace("-", "_")

    expected_suffix = f"{gazette_number}_E_{normalized_date_str}.json"

    matching_files = [
        f for f in MINDEP_INPUT_DIR.iterdir()
        if f.is_file() and f.name.endswith(expected_suffix) and f.name.startswith("ministry-")
    ]

    if not matching_files:
        raise FileNotFoundError(
            f"Gazette file for {gazette_number}, {date_str} not found."
        )

    if len(matching_files) > 1:
        print(f"Multiple gazette files found, using the first one: {matching_files[0].name}")

    json_path = matching_files[0]
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {json_path}: {e}")
    

def load_person_gazette_data_from_JSON(gazette_number: str, date_str: str) -> dict:
    """
    Load a gazette JSON file using gazette number and date.
    Expected file name:
    - persons-<gazette_number>_E_<date_str>.json

    Example:
    - persons-2289-43_E_2022-07-22.json


    Note: date_str passed with hyphens ('YYYY-MM-DD') will be
    converted to underscores to match filenames.
    """

    # Convert hyphens to underscores so "2022-07-22" matches "2022_07_22"
    normalized_date_str = date_str.replace("-", "_")

    expected_suffix = f"{gazette_number}_E_{normalized_date_str}.json"

    matching_files = [
        f for f in PERSON_INPUT_DIR.iterdir()
        if f.is_file() and f.name.endswith(expected_suffix) and f.name.startswith("persons-")
    ]

    if not matching_files:
        raise FileNotFoundError(
            f"Gazette file for {gazette_number}, {date_str} not found."
        )

    if len(matching_files) > 1:
        print(f"⚠️ Multiple gazette files found, using the first one: {matching_files[0].name}")

    json_path = matching_files[0]
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {json_path}: {e}")