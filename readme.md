# Gazette Processor API

A FastAPI backend for tracking and versioning structural changes in Sri Lankan government gazettes. Supports:
- **MinDep**: Ministries and Departments (structural changes: ADD, TERMINATE, MOVE)
- **Person**: Person-portfolio assignments (appointments, removals)

---

## Features
- Track and version changes in ministries/departments and person-portfolio assignments
- Detect and classify transactions: `ADD`, `TERMINATE`, `MOVE`, `RENAME`
- Expose REST API endpoints for loading, reviewing, applying, and resetting state
- Maintain versioned state snapshots for rollback/history
- Output CSVs for transactions

---

## Project Structure

```
.
├── main.py                      # FastAPI application entrypoint
├── csv_writer.py                # CSV output for transactions
├── utils.py                     # Utility functions (JSON loading, etc.)
├── database_handlers/           # DB logic for MinDep and Person
│   ├── mindep_database_handler.py
│   └── person_database_handler.py
├── db_connections/              # DB connection/init for MinDep and Person
│   ├── db_gov.py
│   └── db_person.py
├── gazette_processors/          # Gazette parsing and transaction detection
│   ├── mindep_gazette_processor.py
│   └── person_gazette_processor.py
├── input/                       # Gazette input files (by type/date/gazette)
│   ├── mindep/
│   └── person/
├── output/                      # Output CSVs (by type/date/gazette)
├── request_body/                # Sample request payloads
├── routes/                      # FastAPI routers for endpoints
│   ├── mindep_router.py
│   ├── person_router.py
│   └── state_router.py
├── schemas/                     # DB schema (SQL)
├── state/                       # Versioned state snapshots (by type)
│   ├── mindep/
│   └── person/
├── state_managers/              # State snapshot management
│   ├── mindep_state_manager.py
│   ├── person_state_manager.py
│   └── state_manager.py
└── readme.md
```

---

## Setup

1. **Install dependencies**
   ```bash
   pip install fastapi uvicorn rapidfuzz nltk
   # For some FastAPI features:
   pip install python-multipart
   ```

2. **Initialize databases**
   ```bash
   python main.py
   # This creates SQLite DBs for both MinDep and Person.
   ```

3. **Run the API**
   ```bash
   uvicorn main:app --reload
   ```

4. **Ensure required folders exist**
   ```bash
   # On Unix/Linux/macOS:
   mkdir -p state/mindep state/person input/mindep input/person output/mindep output/person
   # On Windows PowerShell:
   New-Item -ItemType Directory -Force -Path state\mindep, state\person, input\mindep, input\person, output\mindep, output\person
   ```

---

## Input Formats

### MinDep Initial Gazette
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

### MinDep Amendment Gazette
For `/mindep/amendment/{date}/{gazette_number}`:
```json
{
  "ADD": [
    { "ministry_name": "Minister of X", "affected_column": "II", "details": ["Inserted: item 4 — Department Y"] }
  ],
  "OMIT": [
    { "ministry_name": "Minister of Y", "affected_column": "II", "details": ["Omitted: item 6"] }
  ]
}
```

### Person Gazette (ADD/TERMINATE/RENAME)
For `/person/{date}/{gazette_number}`:
```json
{
  "ADD": [
    { "name": "Hon. Kabir Hashim", "Ministry": "Ministry of Roads and Highways", "date": "2018-07-15", "position": "Minister" }
  ],
  "TERMINATE": [
    { "name": "Hon. Thalatha Atukorale", "Ministry": "Ministry of Justice and Prison Reforms", "date": "2018-07-15", "position": "Minister" }
  ],
  "RENAME": [
    { "name": "Dr. Sarath Amunugama", "old ministry": "Ministry of Skills Development & Vocational Training", "new ministry": "Ministry of Skills Development, Vocational Training and Innovation", "date": "2018-06-20", "position": "Minister" }
  ]
}
```

---

## Request Bodies

- Many POST endpoints require a JSON request body. The expected structure depends on the endpoint:

### MinDep Initial Gazette (POST)
- **Endpoint:** `/mindep/initial/{date}/{gazette_number}`
- **Body:**
  ```json
  {
    "ministers": [
      { "name": "Minister of X", "departments": ["Dept A", "Dept B"] }
    ]
  }
  ```

### MinDep Amendment Gazette (POST)
- **Endpoint:** `/mindep/amendment/{date}/{gazette_number}`
- **Body:**
  ```json
  {
    "transactions": {
      "moves": [ ... ],
      "adds": [ ... ],
      "terminates": [ ... ]
    }
  }
  ```
  - See `request_body/mindep/first_amendment.json` and `second_amendment.json` for real examples.

### Person Gazette (POST)
- **Endpoint:** `/person/{date}/{gazette_number}`
- **Body:**
  ```json
  {
    "transactions": {
      "moves": [ ... ],
      "adds": [ ... ],
      "terminates": [ ... ]
    }
  }
  ```
  - See `request_body/person/first_amendment.json` and `second_amendment.json` for real examples.

- **Sample payloads:**
  - The `request_body/` directory contains example JSON files for both MinDep and Person endpoints. Use these as templates for your API requests or for testing with tools like Postman or curl.

---

## API Endpoints

### MinDep Endpoints
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

### Person Endpoints
| Endpoint                                         | Method | Description                                                      |
| ------------------------------------------------ | ------ | ---------------------------------------------------------------- |
| `/person/state/latest`                           | GET    | Get latest saved persons and their portfolios                    |
| `/person/state/{date}`                           | GET    | Get state(s) for a specific date; returns gazette numbers if multiple |                   
| `/person/state/{date}/{gazette_number}`          | GET    | Get a specific person and portfolio state by date and gazette number |
| `/person/{date}/{gazette_number}`                | GET    | Preview predicted transactions from person gazette               |
| `/person/{date}/{gazette_number}`                | POST   | Apply reviewed transactions to DB & save snapshot (**Body:** JSON with `transactions` array) |
| `/person/state/reset`                            | DELETE | Deletes all Person state files and DB                            |

### System
| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/`      | GET    | Health check/status message |

---

## Workflows

### MinDep Flow
1. **Load initial state** from input file (JSON)
2. **Review** tabular content via GET endpoint
3. **POST** reviewed content to create initial state
4. **GET** amendment transactions (MOVE, ADD, TERMINATE) for review
5. **POST** reviewed transactions to update state
6. **Repeat** for further amendments
7. Each amendment is compared to previous state; transactions are applied to DB and a new JSON snapshot is saved

### Person Flow
1. **Load person gazette** (JSON with ADD/TERMINATE/RENAME)
2. **GET** predicted transactions for review
3. **POST** reviewed transactions to update state
4. **Repeat** for further gazettes
5. Each change is applied to DB and a new JSON snapshot is saved

---

## CSV Output

- Transaction CSVs are generated in the `output/` directory, organized by type, date, and gazette number (e.g., `output/mindep/2022-09-16/2297-78/`).
- For each processed gazette, CSV files are created for `ADD`, `MOVE`, and `TERMINATE` transactions.
- **Sample MinDep CSV row:**
  ```csv
  transaction_id,parent,parent_type,child,child_type,rel_type,date
  2297-78_tr_01,Minister of Labour,minister,Vocational Training Authority,department,AS_DEPARTMENT,2022-09-16
  ```
- **Sample Person CSV row:**
  ```csv
  type,name,Ministry,date,position
  ADD,Hon. John Doe,Ministry of Roads and Highways,2018-07-15,Minister
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

## Error Handling

- The API returns JSON error messages for missing files, invalid requests, or not found resources. Example:
  ```json
  { "error": "Gazette file for 2297-78, 2022-09-16 not found." }
  ```
- Always check the response for an `error` key if your request fails.
- The backend prints warnings to the console for missing or duplicate data.

---

## Developer Notes
- The system relies on department/person position for parsing and matching for mindep
- MOVEs are inferred by matching omitted/added names
- RENAMEs are detected for person gazettes when ministry/portfolio names change (TO DO)
- Input/output file naming conventions are important (see `utils.py`)
- **Stemming, Fuzzy Matching, and Scores:**
  - For person gazettes, the system uses stemming (via NLTK's PorterStemmer) and fuzzy string matching (via RapidFuzz) to compare ministry/portfolio names.
  - Ministry/portfolio names are lowercased, stopwords removed, and stemmed before comparison.
  - Fuzzy matching computes a similarity score (token sort ratio) between new and existing ministry/portfolio names.
  - If the score exceeds a threshold (default 70) or there is word overlap, the system suggests possible terminates for adds and moves.
  - These suggestions, along with their scores, are included in the API response to help users review and confirm transactions.

---

## Testing
- Use `curl` or Postman to test endpoints
- See `input/` for sample gazette files and dates/gazette numbers
- See `request_body/` for sample request payloads

Example:
```bash
curl http://127.0.0.1:8000/mindep/amendment/2022-09-16/2297-78
curl http://127.0.0.1:8000/person/2022-09-16/2068-06
```

