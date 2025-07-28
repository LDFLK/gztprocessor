# gztprocessor

A Python library for tracking and versioning structural changes in Sri Lankan government gazettes, with optional FastAPI backend.

Supports:
- **MinDep**: Ministries and Departments (structural changes: ADD, TERMINATE, MOVE)
- **Person**: Person-portfolio assignments (appointments, removals)

---

## Features

- Process extracted details for ministries/departments and person-portfolio assignments (JSON format)
- Detect and classify transactions: `ADD`, `TERMINATE`, `MOVE`, `RENAME`
- Maintain versioned state snapshots for rollback/history
- Output CSVs for transactions (to seed Neo4j)
- [Optional] Expose a FastAPI backend for interactive review and state management

---

## Installation

```bash
pip install git+https://github.com/sehansi-9/gztprocessor.git
# or, for development:
pip install -e .
# To enable API features:
pip install "git+https://github.com/sehansi-9/gztprocessor.git#egg=gztprocessor[api]"

```

---

## Optional: Running the FastAPI Backend

If you want to use the interactive API:

1. Install API dependencies:
   ```bash
   pip install gztprocessor[api]
   ```

2. Run the API server:
   ```bash
   uvicorn main:app --reload
   ```

3. The API exposes endpoints for loading, reviewing, applying, and resetting state.  
   See the **API Endpoints** section below.

---

## Project Structure

```
gztprocessor/
  ├── database_handlers/
  ├── gazette_processors/
  ├── db_connections/
  ├── state_managers/
  ├── schemas/
  ├── csv_writer.py
  └── __init__.py
main.py
MANIFEST.in
setup.py
readme.md
```

---

## Input Formats

### MinDep Initial Gazette
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

### MinDep Amendment Gazette
```json
{
  "ADD": [ ... ],
  "OMIT": [ ... ]
}
```

### Person Gazette
```json
{
  "ADD": [ ... ],
  "TERMINATE": [ ... ],
  "RENAME": [ ... ]
}
```

---

## Request Bodies (for API POST endpoint functions)

- See the `request_body/` directory for real examples.

### MinDep Initial Gazette (POST)
```json
{
  "ministers": [
    { "name": "Minister of X", "departments": ["Dept A", "Dept B"] }
  ]
}
```

### MinDep Amendment Gazette (POST)
```json
{
  "transactions": {
    "moves": [ ... ],
    "adds": [ ... ],
    "terminates": [ ... ]
  }
}
```

### Person Gazette (POST)
```json
{
  "transactions": {
    "moves": [ ... ],
    "adds": [ ... ],
    "terminates": [ ... ]
  }
}
```

---

## CSV Output

- CSVs are generated in `output/`, organized by type, date, and gazette number.
- **Sample MinDep CSV row:**
  ```csv
  transaction_id,parent,parent_type,child,child_type,rel_type,date
  2297-78_tr_01,Minister of Labour,minister,Vocational Training Authority,department,AS_DEPARTMENT,2022-09-16
  ```
- **Sample Person CSV row:**
  ```csv
  transaction_id,parent,parent_type,child,child_type,rel_type,date
  2067-09_tr_01,"Ministry of Science, Technology & Research",minister,Hon. John Doe,person,AS_APPOINTED,2018-04-12
  ```

---

## State Snapshots

- Snapshots are saved as JSON in `state/mindep/` and `state/person/`.
- **MinDep Example:**
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
- **Person Example:**
  ```json
  {
    "persons": [
      {
        "person_name": "Hon. John Doe",
        "portfolios": [
          { "name": "Ministry of Roads and Highways", "position": "Minister" }
        ]
      }
    ]
  }
  ```

---

## API Endpoints (if using FastAPI)

| Endpoint                                         | Method | Description                                                      |
| ------------------------------------------------ | ------ | ---------------------------------------------------------------- |
| `/mindep/state/latest`                           | GET    | Get latest saved state (gazette number, date, state)             |
| `/mindep/state/{date}`                           | GET    | Get state(s) for a specific date; returns gazette numbers if multiple |
| `/mindep/state/{date}/{gazette_number}`          | GET    | Get a specific state by date and gazette number                  |
| `/mindep/initial/{date}/{gazette_number}`        | GET    | Preview contents of initial gazette                              |
| `/mindep/initial/{date}/{gazette_number}`        | POST   | Create initial state in DB & save snapshot (**Body:** JSON with `ministers` array) |
| `/mindep/amendment/{date}/{gazette_number}`      | GET    | Detect transactions from amendment                               |
| `/mindep/amendment/{date}/{gazette_number}`      | POST   | Apply confirmed transactions to DB & snapshot (**Body:** JSON with `transactions` object) |
| `/mindep/state/reset`                            | DELETE | Deletes all MinDep state files and DB                            |
| `/person/state/latest`                           | GET    | Get latest saved persons and their portfolios                    |
| `/person/state/{date}`                           | GET    | Get state(s) for a specific date; returns gazette numbers if multiple |
| `/person/state/{date}/{gazette_number}`          | GET    | Get a specific person and portfolio state by date and gazette number |
| `/person/{date}/{gazette_number}`                | GET    | Preview predicted transactions from person gazette               |
| `/person/{date}/{gazette_number}`                | POST   | Apply reviewed transactions to DB & save snapshot (**Body:** JSON with `transactions` object) |
| `/person/state/reset`                            | DELETE | Deletes all Person state files and DB                            |
| `/`                                             | GET    | Health check/status message                                      |

---

### Summary Table

| Endpoint Type         | Main Function(s) Called                                 | Purpose                                      |
|----------------------|--------------------------------------------------------|----------------------------------------------|
| MinDep Initial        | `extract_initial_gazette_data`, `load_initial_state_to_db` | Extract/load initial ministry structure      |
| MinDep Amendment      | `process_amendment_gazette`, `apply_transactions_to_db`    | Detect/apply department changes              |
| Person Gazette        | `process_person_gazette`, `apply_transactions_to_db`       | Detect/apply person-portfolio changes        |
| State Management      | `get_latest_state`, `get_state_by_date`, `load_state`, `clear_all_state_data` | Manage and reset state snapshots             |

---

## Error Handling

- The API returns JSON error messages for missing files, invalid requests, or not found resources.
- Always check the response for an `error` key if your request fails.
- The backend prints warnings to the console for missing or duplicate data.

---

## Developer Notes

- The system relies on department/person position for parsing and matching (for mindep)
- MOVEs are inferred by matching omitted/added names
- RENAMEs are detected for person gazettes when ministry/portfolio names change 
- Input/output file naming conventions are important (see `utils.py`)
- **Stemming, Fuzzy Matching, and Scores:**
  - For person gazettes, the system uses stemming (via NLTK's PorterStemmer) and fuzzy string matching (via RapidFuzz) to compare ministry/portfolio names.
  - Fuzzy matching computes a similarity score (token sort ratio) between new and existing ministry/portfolio names.
  - If the score exceeds a threshold (default 70) or there is word overlap, the system suggests possible terminates for adds and moves.
  - These suggestions, along with their scores, are included in the API response to help users review and confirm transactions.

---

## Testing

- Use `curl` or Postman to test endpoints (if using the API)
- See `input/` for sample gazette files and dates/gazette numbers
- See `request_body/` for sample request payloads
- See https://github.com/sehansi-9/test-gztprocessor for a sample use of gztprocessor
---

## License

See [LICENSE](LICENSE).

