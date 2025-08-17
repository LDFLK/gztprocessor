import json
from gztprocessor.db_connections.db_trans import get_connection 

def create_record(gazette_number: str, gazette_type: str, gazette_format: str, gazette_date: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (gazette_number, gazette_type, gazette_format, gazette_date)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM transactions WHERE gazette_number = ?
            )
            """,
            (gazette_number, gazette_type, gazette_format, gazette_date, gazette_number)
        )
        conn.commit()



def get_gazette_info(gazette_number: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT gazette_type, gazette_format FROM transactions WHERE gazette_number = ?",
            (gazette_number,)
        )
        row = cur.fetchone()
        return {"gazette_type": row[0], "gazette_format": row[1]} if row else None


def save_transactions(gazette_number: str, data_json: dict):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE transactions SET transactions = ? WHERE gazette_number = ?
            """,
            (json.dumps(data_json), gazette_number)
        )
        conn.commit()

def get_saved_transactions(gazette_number: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT transactions FROM transactions WHERE gazette_number = ?",
            (gazette_number,)
        )
        row = cur.fetchone()
        if not row or row[0] is None:
            return {"transactions": [], "moves": []}
        return json.loads(row[0])  # Now returns entire saved object with transactions and moves

def get_gazettes_by_president(gazette_type: str, from_date: str, to_date: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT gazette_number, gazette_date, warning, gazette_format
            FROM transactions 
            WHERE gazette_type = ? 
              AND gazette_date >= ? 
              AND gazette_date <= ?
            ORDER BY gazette_date, gazette_number
            """,
            (gazette_type, from_date, to_date)
        )
        rows = cur.fetchall()
        return [{"gazette_number": r[0], "date": r[1], "warning":  bool(r[2]), "gazette_format": r[3]} for r in rows]

def set_warning(gazette_number: str, warning: bool):
    """
    Set or clear the warning flag for a given gazette number.
    
    :param gazette_number: The gazette number to update
    :param warning: True to set warning, False to clear it
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE transactions
            SET warning = ?
            WHERE gazette_number = ?
            """,
            (1 if warning else 0, gazette_number)
        )
        conn.commit()
