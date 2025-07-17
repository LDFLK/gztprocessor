-- schema.sql
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS minister;

CREATE TABLE ministry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ministry_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY(ministry_id) REFERENCES ministry(id)
);
