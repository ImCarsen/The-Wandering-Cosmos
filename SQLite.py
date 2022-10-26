import sqlite3 as sl

con = sl.connect('info2.db')

with con:
    con.execute("""
        CREATE TABLE USER (
            number INTEGER,
            name TEXT
        );
    """)