import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Dict, Any


class DocumentInfo:

    """
    Document / Edition 情報を扱うデータアクセスクラス

    ・最新版は edition_status = LATEST(0) で保証
    ・修正中 = DRAFT(1)
    ・旧版 / 廃止 = ARCHIVED(9)
    ・JOIN による一覧取得を基本とする
    """
    # -------------------------------
    # Edition status 定数（ここ！）
    # -------------------------------
    LATEST = 0
    DRAFT = 1
    ARCHIVED = 9

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

    # -------------------------------
    # ステータス → 表示文字列
    # -------------------------------
    @classmethod
    def status_text(cls, status_value: int) -> str:
        return {
            cls.LATEST: "最新",
            cls.DRAFT: "修正中",
            cls.ARCHIVED: "旧版/廃止"
        }.get(status_value, "不明")



    # ------------------------------------------------------------------
    # 全 Edition 一覧
    # ------------------------------------------------------------------
    def fetch_all_editions(self) -> List[Tuple]:
        sql = """
        SELECT
            d.document_number,
            d.document_name,
            e.edition_no,
            e.effective_date,
            e.edition_status,
            e.pdf_path
        FROM Document_Edition_Master AS e
        JOIN document_master AS d
            ON e.document_id = d.document_id
        ORDER BY d.document_number, e.edition_no
        """
        with self._connect() as conn:
            return conn.execute(sql, (self.LATEST,)).fetchall()

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
                d.document_number,
                d.document_name,
                e.edition_no,
                e.effective_date,
                e.edition_status,
                e.pdf_path
            FROM Document_Edition_Master AS e
            JOIN document_master AS d
                ON e.document_id = d.document_id
            WHERE e.edition_status = ?
            ORDER BY d.document_number, e.edition_no
        """
        with self._connect() as conn:
            return conn.execute(sql, (self.LATEST,)).fetchall()

    # ------------------------------------------------------------------
    # Edition 状態別一覧（修正中・旧版など）
    # ------------------------------------------------------------------
    def fetch_editions_by_status(self, edition_status: int) -> List[Tuple]:
        sql = """
        SELECT
            d.document_number,
            d.document_name,
            e.edition_no,
            e.effective_date,
            e.edition_status,
            e.pdf_path
        FROM Document_Edition_Master AS e
        JOIN Document_Master AS d
            ON e.document_id = d.document_id
        WHERE e.edition_status = 0
        ORDER BY d.document_number, e.edition_no
        """
        with self._connect() as conn:
            return conn.execute(sql, (edition_status,)).fetchall()
        
    # ------------------------------------------------------------------
    # 文書単位：Edition 履歴取得
    # ------------------------------------------------------------------
    def fetch_editions_by_document(self, edition_status: int) -> List[Tuple]:
        return self.fetch_editions_by_status(edition_status)

    # ------------------------------------------------------------------
    # 最新版切替（承認処理）
    # ------------------------------------------------------------------
    def approve_edition(self, document_id: int, edition_id: int):
        """
        修正中版を最新版に昇格
        ・現在の最新版 → ARCHIVED
        ・指定 edition → LATEST
        """
        with self._connect() as conn:
            # 現在の最新版を旧版へ
            conn.execute(
                """
                UPDATE Document_Edition_Master
                SET edition_status = ?
                WHERE document_id = ?
                  AND edition_status = ?
                """,
                (self.ARCHIVED, document_id, self.LATEST)
            )

            # 指定版を最新版へ
            conn.execute(
                """
                UPDATE Document_Edition_Master
                SET edition_status = ?
                WHERE edition_id = ?
                """,
                (self.LATEST, edition_id)
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
        sql = """
        INSERT INTO Document_Edition_Master
        (
            document_id,
            edition_no,
            edition_code,
            effective_date,
            edition_status
        )
        VALUES (?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            conn.execute(
                sql,
                (
                    document_id,
                    edition_no,
                    edition_code,
                    effective_date,
                    self.DRAFT
                )
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