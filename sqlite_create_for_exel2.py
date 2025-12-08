import pandas as pd
import sqlite3

# Excel ファイルパス
excel_file = r"C:\DataBase\document_master.xlsx"

# SQLite データベースファイル
db_file = r"C:\DataBase\document_master.db"

# 読み込むシート名（無ければデフォルトの1枚目）
sheet_name = "Document_Edition_Master"

# Excel を読み込み
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# SQLite に接続（無ければ作成される）
conn = sqlite3.connect(db_file)

# テーブル名（好きに変更可能）
table_name = "Document_Edition_Master"

# 書き込み（if_exists='replace' で既存テーブルを上書き）
df.to_sql(table_name, conn, if_exists='replace', index=False)

conn.close()

print("Excel → SQLite の変換が完了しました。")
