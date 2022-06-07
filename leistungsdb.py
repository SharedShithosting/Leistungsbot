import sqlite3 as sl


class LeistungsID(object):
    def __init__(self):
        self.con = sl.connect('leistungs.db')

    def create_history_table(self):
        with self.con:
            self.con.execute("""
                CREATE TABLE USER (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    age INTEGER
                );
            """)
