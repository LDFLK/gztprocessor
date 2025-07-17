import csv
from pathlib import Path

def generate_initial_add_csv(gazette_number: str, date_str: str, structure: list[dict]):
    output_dir = Path("output") / "mindep"/ date_str / gazette_number
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "add.csv"
    rows = []
    counter = 1

    # 1. Ministers → AS_MINISTER
    for minister in structure:
        transaction_id = f"{gazette_number}_tr_{counter:02d}"
        rows.append({
            "transaction_id": transaction_id,
            "parent": "Government of Sri Lanka",
            "parent_type": "government",
            "child": minister["name"],
            "child_type": "minister",
            "rel_type": "AS_MINISTER",
            "date": date_str
        })
        counter += 1

    # 2. Departments → AS_DEPARTMENT
    for minister in structure:
        for dept in minister["departments"]:
            transaction_id = f"{gazette_number}_tr_{counter:02d}"
            rows.append({
                "transaction_id": transaction_id,
                "parent": minister["name"],
                "parent_type": "minister",
                "child": dept,
                "child_type": "department",
                "rel_type": "AS_DEPARTMENT",
                "date": date_str
            })
            counter += 1

    # Write CSV
    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "transaction_id", "parent", "parent_type", "child", "child_type", "rel_type", "date"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ CSV created at: {csv_path}")

def generate_amendment_csvs(gazette_number: str, date_str: str, transactions: list[dict]):
    """
    Generate 3 separate CSVs (add.csv, terminate.csv, move.csv) from amendment transactions.
    Formats:
    - ADD, TERMINATE: transaction_id,parent,parent_type,child,child_type,rel_type,date
    - MOVE: transaction_id,old_parent,new_parent,child,type,date
    """
    output_dir = Path("output") / "mindep"/  date_str / gazette_number
    output_dir.mkdir(parents=True, exist_ok=True)

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
                "rel_type": "REMOVED_DEPARTMENT",
                "date": date_str
            })

        elif tx["type"] == "MOVE":
            move_rows.append({
                "transaction_id": transaction_id,
                "old_parent": tx["from_ministry"],
                "new_parent": tx["to_ministry"],
                "child": tx["department"],
                "type": "MOVE",
                "date": date_str
            })

        counter += 1

    # Write ADD
    if add_rows:
        with open(output_dir / "add.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "parent", "parent_type",
                "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(add_rows)
        print(f"✅ ADD CSV written to: {output_dir / 'add.csv'}")

    # Write TERMINATE
    if terminate_rows:
        with open(output_dir / "terminate.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "parent", "parent_type",
                "child", "child_type", "rel_type", "date"
            ])
            writer.writeheader()
            writer.writerows(terminate_rows)
        print(f"✅ TERMINATE CSV written to: {output_dir / 'terminate.csv'}")

    # Write MOVE
    if move_rows:
        with open(output_dir / "move.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "transaction_id", "old_parent", "new_parent",
                "child", "type", "date"
            ])
            writer.writeheader()
            writer.writerows(move_rows)
        print(f"✅ MOVE CSV written to: {output_dir / 'move.csv'}")
