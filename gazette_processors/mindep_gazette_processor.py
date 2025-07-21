from pathlib import Path
import re
from collections import defaultdict
from db_connections.db_gov import get_connection
from state_managers.mindep_state_manager import MindepStateManager
import utils

mindep_state_manager = MindepStateManager()

def extract_initial_gazette_data(gazette_number: str, date_str: str) -> dict:
    data = utils.load_mindep_gazette_data_from_JSON(gazette_number, date_str)
    ministries = data.get("ministers", [])
    if not ministries:
        raise ValueError(
            f"No ministries found in input file for gazette {gazette_number} on {date_str}"
        )
    return ministries

# TODO: Resolve this issue for renames: https://github.com/zaeema-n/orgchart_nexoan/issues/11#issue-3238949430

def extract_column_II_department_changes(gazette_number: str, date_str: str) -> tuple[list[dict], list[dict]]:
    data = utils.load_mindep_gazette_data_from_JSON(gazette_number, date_str)

    adds = [e for e in data.get("ADD", []) if e.get("affected_column") == "II"]
    omits = [e for e in data.get("OMIT", []) if e.get("affected_column") == "II"]

    added_map = defaultdict(list)
    for entry in adds:
        ministry_name = entry.get("ministry_name")
        if not ministry_name:
            print(f"⚠️ Ministry name missing in ADD entry: {entry}")
            continue

        for detail in entry.get("details", []):
            match = re.match(
                r"Inserted:\s*(?:item\s*(\d+)\s*\u2014\s*)?(.*?)(?:\s+after item\s+\d+)?$",
                detail.strip(),
                flags=re.IGNORECASE,
            )
            if match:
                position = match.group(1)
                department_name = match.group(2).strip()
                added_map[ministry_name].append(
                    {
                        "name": department_name,
                        "position": int(position) if position else None,
                    }
                )
            else:
                print(f"⚠️ Could not parse ADD line: '{detail}' in {ministry_name}")

    added_departments = [
        {"ministry_name": ministry, "departments": depts}
        for ministry, depts in added_map.items()
    ]

    removed_departments_raw = []
    for entry in omits:
        ministry_name = entry.get("ministry_name")
        if not ministry_name:
            print(f"⚠️ Ministry name missing in OMIT entry: {entry}")
            continue
        positions = []
        for detail in entry.get("details", []):
            numbers = re.findall(
                r"Omitted.*?item[s]?\s*([\d,\sand]+)", detail, flags=re.IGNORECASE
            )
            if numbers:
                raw = numbers[0]
                digits = re.findall(r"\d+", raw)
                positions.extend(int(n) for n in digits)
            else:
                print(f"⚠️ Could not parse OMIT line: '{detail}' in {ministry_name}")
        if positions:
            removed_departments_raw.append(
                {"ministry_name": ministry_name, "omitted_positions": positions}
            )

    return added_departments, removed_departments_raw


def resolve_omitted_items(removed_departments_raw: list[dict], gazette_number: str, date_str: str) -> list[dict]:
    resolved = []
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            prev_gazette_number, prev_date = mindep_state_manager.get_latest_state_info(cur, gazette_number, date_str)

            for entry in removed_departments_raw:
                ministry = entry["ministry_name"]
            
                # Select ministry id for the previous gazette_number and date
                cur.execute("SELECT id FROM ministry WHERE name = ? AND gazette_number = ? AND date = ?", (ministry, prev_gazette_number, prev_date))
                result = cur.fetchone()
                if not result:
                    print(
                        f"⚠️ Ministry '{ministry}' not found in DB (for gazette {prev_gazette_number} on {prev_date})"
                    )
                    continue
                ministry_id = result[0]

                if "omitted_positions" in entry:
                    for pos in sorted(entry["omitted_positions"], reverse=True):
                        cur.execute(
                            """
                            SELECT name FROM department
                            WHERE ministry_id = ? AND position = ? AND gazette_number = ? AND date = ?
                            """,
                            (ministry_id, pos, prev_gazette_number, prev_date),
                        )
                        row = cur.fetchone()
                        if row:
                            dept_name = row[0]
                            resolved.append(
                                {"ministry": ministry, "department": dept_name}
                            )
                        else:
                            print(
                                f"⚠️ No department at position {pos} under {ministry} (gazette {prev_gazette_number} on {prev_date})"
                            )

                elif "omitted_names" in entry:
                    for name in entry["omitted_names"]:
                        resolved.append({"ministry": ministry, "department": name})

    except Exception as e:
        print(f"❗ Error resolving omitted items from DB: {e}")
        return []

    return resolved


def classify_department_changes(added: list[dict], removed: list[dict]) -> dict:
    def normalize(name: str) -> str:
        return name.strip().lower()

    moves = []
    adds_list = []
    terminates = []
    added_map = {}

    for item in added:
        for dept_entry in item["departments"]:
            raw_name = dept_entry["name"]
            name = normalize(raw_name)
            added_map[name] = {
                "original_name": raw_name,
                "ministry": item["ministry_name"],
                "position": dept_entry.get("position"),
            }

    removed_map = {}
    for item in removed:
        name = normalize(item["department"])
        removed_map[name] = item["ministry"]

    processed = set()

    print("\n Matching departments for MOVEs...")
    for dept, from_min in removed_map.items():
        if dept in added_map:
            to_entry = added_map[dept]
            moves.append(
                {
                    "type": "MOVE",
                    "department": to_entry["original_name"],
                    "from_ministry": from_min,
                    "to_ministry": to_entry["ministry"],
                    "position": to_entry["position"],
                }
            )
            processed.add(dept)
            print(f"- MOVE detected: {to_entry['original_name']} from {from_min} → {to_entry['ministry']}")

    print("\n Remaining ADDs...")
    for dept, to_entry in added_map.items():
        if dept not in processed:
            adds_list.append(
                {
                    "type": "ADD",
                    "department": to_entry["original_name"],
                    "to_ministry": to_entry["ministry"],
                    "position": to_entry["position"],
                }
            )
            print(f"- ADD: {to_entry['original_name']} → {to_entry['ministry']}")

    print("\n Remaining TERMINATEs...")
    for dept, from_min in removed_map.items():
        if dept not in processed:
            terminates.append(
                {
                    "type": "TERMINATE",
                    "department": dept.title(),
                    "from_ministry": from_min,
                }
            )
            print(f"- TERMINATE: {dept.title()} from {from_min}")

    return {
        "transactions": {
            "moves": moves,
            "adds": adds_list,
            "terminates": terminates
        }
    }



def process_amendment_gazette(gazette_number: str, date_str: str) -> list[dict]:
    try:
        added, removed_raw = extract_column_II_department_changes(gazette_number, date_str)
    except ValueError as e:
        print(f" Failed to extract column II changes for gazette {gazette_number} on {date_str}: {e}")
        return []

    resolved_removed = resolve_omitted_items(removed_raw, gazette_number, date_str)
    transactions = classify_department_changes(added, resolved_removed)

    return transactions
