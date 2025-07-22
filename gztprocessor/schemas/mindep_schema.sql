-- schema.sql
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS ministry;

CREATE TABLE ministry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    gazette_number TEXT NOT NULL,
    date TEXT NOT NULL
);

CREATE TABLE department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ministry_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    gazette_number TEXT NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY(ministry_id) REFERENCES ministry(id)
);
