#  Gazette Processor API (MinDep)

This FastAPI backend processes government gazette data to track structural changes in ministries and departments over time, including `ADD`, `TERMINATE`, and `MOVE` operations. It maintains versioned state snapshots and exposes API endpoints to inspect, apply, and reset changes.

---

##  Project Structure

```
.
├── main.py                 # FastAPI application
├── db.py                   # SQLite DB connection and init
├── utils.py                # Utility functions (loading JSON, etc.)
├── database.py             # DB insert/apply logic for state and transactions
├── gazette_processor.py    # Core logic to classify ADD/OMIT into transactions
├── state_manager.py        # Manage loading/saving versioned state snapshots
├── state/                  # Folder storing versioned state JSONs
└── input/                  # Folder storing gazette input files (by date & gazette number)
```

---

##  Setup

1. **Install dependencies**

   ```bash
   pip install fastapi uvicorn
   ```
   
2. **Initialize database**

   ```bash
   python main.py
   ```

3. **Run the API**

   ```bash
   uvicorn main:app --reload
   ```

4. **Ensure required folders exist**

   ```bash
   mkdir -p state input
   ```

---

## Input Format

### Initial Gazette

For `/mindep/initial/{date}/{gazette_number}`:

```json
{
  "ministers": [
    {
      "name": "Minister of X",
      "departments": ["Dept A", "Dept B", "Dept C"]
    }
  ]
}
```

### Amendment Gazette

For `/mindep/amendment/{date}/{gazette_number}`:

```json
{
  "ADD": [
    {
      "ministry_name": "Minister of X",
      "affected_column": "II",
      "details": ["Inserted: item 4 — Department Y"]
    }
  ],
  "OMIT": [
    {
      "ministry_name": "Minister of Y",
      "affected_column": "II",
      "details": ["Omitted: item 6"]
    }
  ]
}
```

---

## How It Works

1. You load the **initial state** from an input file.
2. The program sends the tabular content for review in GET by date and gazette number
3. Send the request body after reviewing to create initial state
4. GET the first amendment transactions with the detected compound transactions like MOVE, by date and gazette number
5. Review and send the payload to update the state
6. Continue with the second amendment
7. Each **amendment** is compared to the previous state to detect:

   * **MOVEs** (omitted in one ministry, added in another)
   * **ADDs** (new departments)
   * **TERMINATEs** (removed departments that don't reappear)
8. Once reviewed, transactions are applied to the DB and a new JSON state snapshot is saved.

---

##  API Endpoints

###  State

| Endpoint                                         | Method | Description                                                      |
| ------------------------------------------------ | ------ | ---------------------------------------------------------------- |
| `/mindep/state/latest`                           | `GET`  | Get the latest saved state (with gazette number and date)        |
| `/mindep/state/{date}`                           | `GET`  | Get state(s) for a specific date; returns gazette numbers if multiple |
| `/mindep/state/{date}/{gazette_number}`          | `GET`  | Get a specific state by date and gazette number                  |
| `/mindep/state/{date}/{gazette_number}`          | `POST` | Load state snapshot into DB for a specific date and gazette      |

---

### Initial Gazette

| Endpoint                                         | Method | Description                                                      |
| ------------------------------------------------ | ------ | ---------------------------------------------------------------- |
| `/mindep/initial/{date}/{gazette_number}`        | `GET`  | Preview contents of initial gazette for a date and gazette number|
| `/mindep/initial/{date}/{gazette_number}`        | `POST` | Create initial state in DB & save snapshot (see request_body dir to get sample initial gazette payload)|

---

### Amendment Gazette

| Endpoint                                         | Method | Description                                                      |
| ------------------------------------------------ | ------ | ---------------------------------------------------------------- |
| `/mindep/amendment/{date}/{gazette_number}`      | `GET`  | Detect transactions from amendment for a date and gazette number |
| `/mindep/amendment/{date}/{gazette_number}`      | `POST` | Apply confirmed transactions to DB & snapshot (see request_body dir to get sample amendment payloads) |

---

###  Reset System

| Endpoint | Method   | Description                           |
| -------- | -------- | ------------------------------------- |
| `/reset` | `DELETE` | Deletes all snapshots and DB contents |

---

##  Transaction Types

| Type        | Description                                                         |
| ----------- | ------------------------------------------------------------------- |
| `ADD`       | Department newly inserted in a ministry                             |
| `TERMINATE` | Department removed and not found elsewhere                          |
| `MOVE`      | Department omitted in one ministry and added in another (same name) |

---

##  State Snapshot Format

Each state file looks like:

```json
{
  "ministers": [
    {
      "name": "Minister of Finance",
      "departments": [
        "Department of Treasury",
        "Inland Revenue",
        "Customs"
      ]
    }
  ]
}
```

Saved as `state/state_{gazette_number}_{YYYY-MM-DD}.json`.

---

##  Dev Notes

* The system relies on **department position** for parsing.
* MOVEs are inferred by matching omitted department names to added ones.
* Positions are preserved during reordering or reinsertion.
* Snapshots enable rollback, history tracking, and diffing.

---

##  Testing

Use `curl` or Postman to test endpoints. 
See input files to get the dates and gazette numbers.

Example:

```bash
curl http://127.0.0.1:8000/mindep/amendment/2022-09-16/2297-78
```

---

