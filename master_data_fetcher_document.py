import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Optional, Dict, Any


class MasterDataFetcherDocument:
    """
    document_master.db 内のマスタデータを取得するクラス。
    """
    def __init__(self, db_name: str):
        self.db_name = db_name

    @contextmanager
    def _connect(self):
        """データベース接続を共通化"""
        conn = sqlite3.connect(self.db_name)
        try:
            cursor = conn.cursor()
            yield cursor
        finally:
            conn.close()

    # ------------------------------------------------------------
    # 汎用：指定テーブルを全取得
    # ------------------------------------------------------------
    def fetch_all(self, table_name: str) -> List[Tuple[Any, ...]]:
        """
        指定テーブルの全データを取得
        """
        try:
            with self._connect() as cur:
                cur.execute(f"SELECT * FROM {table_name}")
                return cur.fetchall()
        except Exception as e:
            print(f"[fetch_all] エラー: {e}")
            return []

    # ------------------------------------------------------------
    # ID → 名前（または任意カラム）変換
    # ------------------------------------------------------------
    def fetch_value_by_id(self, table_name: str, key_column: str, value_column: str, key_value: Any) -> Optional[Any]:
        """
        指定IDの値を取得
        """
        try:
            with self._connect() as cur:
                sql = f"SELECT {value_column} FROM {table_name} WHERE {key_column} = ?"
                cur.execute(sql, (key_value,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[fetch_value_by_id] エラー: {e}")
            return None

    # ------------------------------------------------------------
    # 任意カラム取得
    # ------------------------------------------------------------
    def fetch_columns(self, table_name: str, columns: List[str]) -> List[Tuple[Any, ...]]:
        """
        指定カラムのみ取得
        """
        col_str = ", ".join(columns)
        try:
            with self._connect() as cur:
                cur.execute(f"SELECT {col_str} FROM {table_name}")
                return cur.fetchall()
        except Exception as e:
            print(f"[fetch_columns] エラー: {e}")
            return []

    # ------------------------------------------------------------
    # 条件検索
    # ------------------------------------------------------------
    def fetch_by_conditions(self, table_name, conditions):
        try:
            with self._connect() as cur:
                cur.execute(f"PRAGMA table_info({table_name})")
                columns = {row[1] for row in cur.fetchall()}

            for key in conditions.keys():
                if key not in columns:
                    raise ValueError(f"カラム '{key}' は {table_name} に存在しません")

            where_clauses = [f"{col} = ?" for col in conditions.keys()]
            sql = f"SELECT * FROM {table_name} WHERE " + " AND ".join(where_clauses)

            with self._connect() as cur:
                cur.execute(sql, tuple(conditions.values()))
                return cur.fetchall()

        except Exception as e:
            print(f"[fetch_by_conditions] エラー: {e}")
            return []


    # ------------------------------------------------------------
    # 1件取得（ID検索）
    # ------------------------------------------------------------
    def fetch_one(self, table_name: str, key_column: str, key_value: Any) -> Optional[Tuple[Any, ...]]:
        """
        指定キーの1レコードだけ取得
        """
        try:
            with self._connect() as cur:
                sql = f"SELECT * FROM {table_name} WHERE {key_column} = ?"
                cur.execute(sql, (key_value,))
                return cur.fetchone()
        except Exception as e:
            print(f"[fetch_one] エラー: {e}")
            return None

    def fetch_latest_documents(self):
        """
        最新版（edition_status = 0）を保証して取得
        """
        sql = """
        SELECT
            d.document_id,
            d.document_number,
            d.document_name,
            e.edition_id,
            e.edition_no,
            e.effective_date,
            e.edition_status
        FROM Document_Master d
        JOIN Document_Edition_Master e
        ON d.document_id = e.document_id
        WHERE e.edition_status = 0
        ORDER BY d.document_number
        """
        try:
            with self._connect() as cur:
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            print(f"[fetch_latest_documents] エラー: {e}")
            return []

    def fetch_editions_by_status(self, edition_status: int):
        """
        edition_status 指定で Edition 一覧取得
        """
        sql = """
        SELECT
            d.document_id,
            d.document_number,
            d.document_name,
            e.edition_id,
            e.edition_no,
            e.effective_date,
            e.edition_status
        FROM Document_Master d
        JOIN Document_Edition_Master e
        ON d.document_id = e.document_id
        WHERE e.edition_status = ?
        ORDER BY d.document_number, e.edition_no
        """
        try:
            with self._connect() as cur:
                cur.execute(sql, (edition_status,))
                return cur.fetchall()
        except Exception as e:
            print(f"[fetch_editions_by_status] エラー: {e}")
            return []
