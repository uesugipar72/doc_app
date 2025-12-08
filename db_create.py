import sqlite3

# DBのフルパス
db_name = r"C:\DataBase\document_master.db"

# SQLite に接続
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# document_edition_master テーブル作成
table_query = """
CREATE TABLE IF NOT EXISTS Document_Edition_Master (
    edition_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         INTEGER NOT NULL,
    edition_no          INTEGER NOT NULL,
    edition_code        TEXT,
    document_full_number TEXT,
    document_path        TEXT,
    effective_date      TEXT,
    end_date            TEXT,
    status              TEXT,    
"""

cursor.execute(table_query)
conn.commit()
conn.close()

print("document_edition_master テーブルを作成しました。")
