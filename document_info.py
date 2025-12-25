import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Dict, Any


class DocumentInfo:
    """
    Document / Edition 情報を扱うデータアクセスクラス
    ・最新版は edition_status = 0 で保証
    ・JOIN による一覧取得を基本とする
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # DB 接続（共通）
    # ------------------------------------------------------------------
    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetch_all_editions(self):
        sql = """
        SELECT
            d.document_number,
            d.document_name,
            e.edition_no,
            e.effective_date,
            e.edition_status
        FROM Document_Master d
        JOIN Document_Edition_Master e
        ON d.document_id = e.document_id
        ORDER BY d.document_number, e.edition_no DESC
        """
        with self._connect() as conn:
            return conn.execute(sql).fetchall()


    # ------------------------------------------------------------------
    # ステータス変換
    # ------------------------------------------------------------------
    @staticmethod
    def status_text(status_value: int) -> str:
        return {
            0: "最新",
            1: "修正中",
            9: "旧版/廃止"
        }.get(status_value, "不明")

    # ------------------------------------------------------------------
    # 最新版ドキュメント一覧（JOIN / 保証版）
    # ------------------------------------------------------------------
    def fetch_latest_documents(self) -> List[Tuple]:
        """
        最新版（edition_status = 0）のみ取得
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
        with self._connect() as conn:
            return conn.execute(sql).fetchall()

    # ------------------------------------------------------------------
    # Edition 状態別一覧（修正中・旧版など）
    # ------------------------------------------------------------------
    def fetch_editions_by_status(self, edition_status: int) -> List[Tuple]:
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
        with self._connect() as conn:
            return conn.execute(sql, (edition_status,)).fetchall()

    # ------------------------------------------------------------------
    # 文書ID指定：全 Edition 取得（履歴用）
    # ------------------------------------------------------------------
    def fetch_editions_by_document(self, document_id: int) -> List[Tuple]:
        sql = """
        SELECT
            edition_id,
            edition_no,
            edition_code,
            effective_date,
            edition_status
        FROM Document_Edition_Master
        WHERE document_id = ?
        ORDER BY edition_no DESC
        """
        with self._connect() as conn:
            return conn.execute(sql, (document_id,)).fetchall()

    # ------------------------------------------------------------------
    # 最新版切替（承認処理）
    # ------------------------------------------------------------------
    def approve_edition(self, document_id: int, edition_id: int):
        """
        修正中版を最新版に昇格
        ・現在の最新版 → 旧版
        ・指定 edition → 最新版
        """
        with self._connect() as conn:
            # 現在の最新版を旧版へ
            conn.execute(
                """
                UPDATE Document_Edition_Master
                SET edition_status = 9
                WHERE document_id = ?
                  AND edition_status = 0
                """,
                (document_id,)
            )

            # 指定版を最新版へ
            conn.execute(
                """
                UPDATE Document_Edition_Master
                SET edition_status = 0
                WHERE edition_id = ?
                """,
                (edition_id,)
            )

    # ------------------------------------------------------------------
    # 修正中版の新規登録
    # ------------------------------------------------------------------
    def create_draft_edition(
        self,
        document_id: int,
        edition_no: int,
        edition_code: str,
        effective_date: str
    ):
        """
        修正中版（edition_status=1）を追加
        """
        sql = """
        INSERT INTO Document_Edition_Master
        (
            document_id,
            edition_no,
            edition_code,
            effective_date,
            edition_status
        )
        VALUES (?, ?, ?, ?, 1)
        """
        with self._connect() as conn:
            conn.execute(
                sql,
                (document_id, edition_no, edition_code, effective_date)
            )

    # ------------------------------------------------------------------
    # 文書マスタ取得（参照用）
    # ------------------------------------------------------------------
    def fetch_document_master(self) -> List[Tuple]:
        sql = """
        SELECT
            document_id,
            document_number,
            document_name
        FROM Document_Master
        ORDER BY document_number
        """
        with self._connect() as conn:
            return conn.execute(sql).fetchall()
