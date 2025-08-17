import os 
from pathlib import Path
import csv

def generate_initial_add_csv(gazette_number: str, date_str: str, structure: list[dict]):
    output_dir = Path("output") / "mindep" / date_str / gazette_number
    output_dir.mkdir(parents=True, exist_ok=True)

    add_rows = []
    move_rows = []
    counter = 1

    # 1. Ministers → AS_MINISTER (always ADD)
    for minister in structure:
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        add_rows.append({
            "transaction_id": transaction_id,
            "parent": "Government of Sri Lanka",
            "parent_type": "government",
            "child": minister["name"],
            "child_type": "minister",
            "rel_type": "AS_MINISTER",
            "date": date_str
        })
        counter += 1

    # 2. Departments → either ADD or MOVE
    for minister in structure:
        for dept in minister["departments"]:
            transaction_id = f"{gazette_number}_tr_{counter:02d}"
            dept_name = dept["name"]
            prev_min = dept.get("previous_ministry")

            if prev_min:
                # MOVE
                move_rows.append({
                    "transaction_id": transaction_id,
                    "old_parent": prev_min,
                    "new_parent": minister["name"],
                    "child": dept_name,
                    "type": "AS_DEPARTMENT",
                    "date": date_str
                })
            else:
                # ADD
                add_rows.append({
                    "transaction_id": transaction_id,
                    "parent": minister["name"],
                    "parent_type": "minister",
                    "child": dept_name,
                    "child_type": "department",
                    "rel_type": "AS_DEPARTMENT",
                    "date": date_str
                })
            counter += 1

    add_csv_path = output_dir / "add.csv"
    if add_rows:
        with open(add_csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "parent", "parent_type", "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(add_rows)
        print(f"✅ ADD CSV created at: {add_csv_path}")
    else:
        if add_csv_path.exists():
            os.remove(add_csv_path)
            print(f"🗑️ No add rows found. Existing add.csv deleted at: {add_csv_path}")
        else:
            print("ℹ️ No add rows and no existing add.csv to delete.")
            
    move_csv_path = output_dir / "move.csv"
    if move_rows:
        with open(move_csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "old_parent", "new_parent", "child", "type", "date"
            ])
            writer.writeheader()
            writer.writerows(move_rows)
        print(f"✅ MOVE CSV created at: {move_csv_path}")
    else:
        if move_csv_path.exists():
            os.remove(move_csv_path)
            print(f"🗑️ No move rows found. Existing move.csv deleted at: {move_csv_path}")
        else:
            print("ℹ️ No move rows and no existing move.csv to delete.")


def generate_amendment_csvs(gazette_number: str, date_str: str, transactions: dict):
    """
    Generate 3 separate CSVs (add.csv, terminate.csv, move.csv) from amendment transactions.
    Formats:
    - ADD, TERMINATE: transaction_id,parent,parent_type,child,child_type,rel_type,date
    - MOVE: transaction_id,old_parent,new_parent,child,type,date
    """
    output_dir = Path("output") / "mindep" / date_str / gazette_number
    output_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(transactions, dict) and "transactions" in transactions:
        transactions = transactions["transactions"]
    if isinstance(transactions, dict):
        transactions = (
            transactions.get("moves", []) +
            transactions.get("adds", []) +
            transactions.get("terminates", [])
        )

    add_rows = []
    terminate_rows = []
    move_rows = []

    counter = 1

    for tx in transactions:
        transaction_id = f"{gazette_number}_tr_{counter:02d}"

        if tx["type"] == "ADD":
            add_rows.append({
                "transaction_id": transaction_id,
                "parent": tx["to_ministry"],
                "parent_type": "minister",
                "child": tx["department"],
                "child_type": "department",
                "rel_type": "AS_DEPARTMENT",
                "date": date_str
            })

        elif tx["type"] == "TERMINATE":
            terminate_rows.append({
                "transaction_id": transaction_id,
                "parent": tx["from_ministry"],
                "parent_type": "minister",
                "child": tx["department"],
                "child_type": "department",
                "rel_type": "AS_DEPARTMENT",
                "date": date_str
            })

        elif tx["type"] == "MOVE":
            move_rows.append({
                "transaction_id": transaction_id,
                "old_parent": tx["from_ministry"],
                "new_parent": tx["to_ministry"],
                "child": tx["department"],
                "rel_type": "AS_DEPARTMENT",
                "date": date_str
            })

        counter += 1

    # Helper to write or delete CSVs
    def write_or_delete_csv(rows, path, fieldnames):
        if rows:
            with open(path, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            print(f"✅ CSV written to: {path}")
        else:
            if path.exists():
                os.remove(path)
                print(f"🗑️ No rows found. Existing CSV deleted at: {path}")
            else:
                print(f"ℹ️ No rows and no existing CSV to delete at: {path}")

    # Write ADD CSV
    csv_path = output_dir / "add.csv"
    write_or_delete_csv(add_rows, csv_path, [
        "transaction_id", "parent", "parent_type",
        "child", "child_type", "rel_type", "date"
    ])

    # Write TERMINATE CSV
    csv_path = output_dir / "terminate.csv"
    write_or_delete_csv(terminate_rows, csv_path, [
        "transaction_id", "parent", "parent_type",
        "child", "child_type", "rel_type", "date"
    ])

    # Write MOVE CSV
    csv_path = output_dir / "move.csv"
    write_or_delete_csv(move_rows, csv_path, [
        "transaction_id", "old_parent", "new_parent",
        "child", "rel_type", "date"
    ])

def generate_person_csvs(gazette_number: str, date_str: str, transactions: dict):
    """
    Generate CSVs for person-related transactions: ADDs, TERMINATEs, MOVEs, RENAMES.
    For RENAMES, generate both TERMINATE (old ministry) and ADD (new ministry) records.
    Formats:
    - ADD/TERMINATE: transaction_id, parent, parent_type, child, child_type, rel_type, date
    - MOVE: transaction_id, old_parent, new_parent, parent_type, child, child_type, rel_type, date
    """
    output_dir = Path("output") / "person" / date_str / gazette_number
    output_dir.mkdir(parents=True, exist_ok=True)

    txs = transactions.get("transactions", transactions)

    move_rows = []
    add_rows = []
    terminate_rows = []

    counter = 1

    # Process ADDs
    for tx in txs.get("adds", []):
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        add_rows.append({
            "transaction_id": transaction_id,
            "parent": tx["new_ministry"],
            "parent_type": tx["new_position"].lower().replace(" ", "_"),
            "child": tx["new_person"],
            "child_type": "person",
            "rel_type": "AS_APPOINTED",
            "date": tx["date"]
        })
        counter += 1

    # Process TERMINATES
    for tx in txs.get("terminates", []):
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        terminate_rows.append({
            "transaction_id": transaction_id,
            "parent": tx["ministry"],
            "parent_type": tx["position"].lower().replace(" ", "_"),
            "child": tx["name"],
            "child_type": "person",
            "rel_type": "AS_APPOINTED",
            "date": tx["date"]
        })
        counter += 1

    # Process MOVES
    for tx in txs.get("moves", []):
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        move_rows.append({
            "transaction_id": transaction_id,
            "old_parent": tx["from_ministry"],
            "new_parent": tx["to_ministry"],
            "parent_type": tx["to_position"].lower().replace(" ", "_"),
            "child": tx["name"],
            "child_type": "person",
            "rel_type": "AS_APPOINTED",
            "date": tx["date"]
        })
        counter += 1

    # Process RENAMES as TERMINATE + ADD
    for tx in txs.get("renames", []):
        name = tx["name"]
        old_ministry = tx["old_ministry"]
        new_ministry = tx["new_ministry"]
        date = tx["date"]

        # TERMINATE from old ministry
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        terminate_rows.append({
            "transaction_id": transaction_id,
            "parent": old_ministry,
            "parent_type": "minister", 
            "child": name,
            "child_type": "person",
            "rel_type": "AS_APPOINTED",
            "date": date
        })
        counter += 1

        # ADD to new ministry
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        add_rows.append({
            "transaction_id": transaction_id,
            "parent": new_ministry,
            "parent_type": "minister",
            "child": name,
            "child_type": "person",
            "rel_type": "AS_APPOINTED",
            "date": date
        })
        counter += 1

    # Write ADD CSV
    if add_rows:
        with open(output_dir / "add.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "parent", "parent_type",
                "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(add_rows)
        print(f"✅ ADD CSV written to: {output_dir / 'add.csv'}")

    # Write TERMINATE CSV
    if terminate_rows:
        with open(output_dir / "terminate.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "parent", "parent_type",
                "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(terminate_rows)
        print(f"✅ TERMINATE CSV written to: {output_dir / 'terminate.csv'}")

    # Write MOVE CSV
    if move_rows:
        with open(output_dir / "move.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "old_parent", "new_parent",
                "parent_type", "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(move_rows)
        print(f"✅ MOVE CSV written to: {output_dir / 'move.csv'}")

