DROP TABLE IF EXISTS portfolio;
DROP TABLE IF EXISTS person;

CREATE TABLE person (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gazette_number TEXT NOT NULL,
    date TEXT NOT NULL
);

CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    person_id INTEGER, 
    gazette_number TEXT NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY(person_id) REFERENCES person(id)
);
