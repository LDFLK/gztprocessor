DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gazette_type TEXT NOT NULL,
    gazette_format TEXT NOT NULL,
    gazette_number TEXT NOT NULL UNIQUE,
    gazette_date TEXT NOT NULL,
    warning INTEGER DEFAULT 0, 
    transactions TEXT DEFAULT '[]' CHECK(json_valid(transactions))

);

