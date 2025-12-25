import sqlite3
from typing import List, Tuple, Optional


class DocumentInfo:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def _connect(self):
        conn = sqlite3.connect(self.db_name)
        return conn

    def fetch_all_documents_for_view(
        self,
        status_filter: Optional[int] = None
    ) -> List[Tuple]:
        """
        文書一覧表示専用・唯一の取得口

        Args:
            status_filter:
                None : 全件
                0    : 最新版のみ
                1    : 修正中のみ
                9    : 廃棄のみ

        Returns:
            (
                document_id,
                document_number,
                document_name,
                edition_no,
                effective_date,
                edition_status
            ) の list
        """

        sql = """
            SELECT
                d.document_id,
                d.document_number,
                d.document_name,
                e.edition_no,
                e.effective_date,
                e.edition_status
            FROM document_master d
            JOIN document_edition_master e
              ON d.document_id = e.document_id
        """

        params = []

        if status_filter is not None:
            sql += " WHERE e.edition_status = ?"
            params.append(status_filter)

        sql += """
            ORDER BY
                d.document_number,
                e.edition_no DESC
        """

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    @staticmethod
    def status_text(status: int) -> str:
        return {
            0: "最新版",
            1: "修正中",
            9: "廃棄"
        }.get(status, "不明")
