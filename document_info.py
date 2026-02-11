import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Dict, Any
import os
import shutil
import datetime

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

    def __init__(self, db_path, base_dir):
        self.db_path = db_path
        self.base_dir = base_dir
        
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
    def fetch_all_editions(
        self,
        status: int | None = None,
        document_number: str = "",
        document_name: str = "",
        date_from: str = "",
        date_to: str = ""
    ) -> list:

        sql = """
        SELECT
            e.document_id      AS document_id,
            d.document_number  AS document_number,
            d.document_name    AS document_name,
            e.edition_no       AS edition_no,
            e.effective_date   AS effective_date,
            e.edition_status   AS edition_status,
            e.pdf_path         AS pdf_path
        FROM Document_Edition_Master e
        JOIN Document_Master d
          ON e.document_id = d.document_id
        WHERE 1=1
        """
        params = []

        if status is not None:
            sql += " AND e.edition_status = ?"
            params.append(status)

        if document_number:
            sql += " AND d.document_number LIKE ?"
            params.append(f"%{document_number}%")

        if document_name:
            sql += " AND d.document_name LIKE ?"
            params.append(f"%{document_name}%")

        if date_from:
            sql += " AND e.effective_date >= ?"
            params.append(date_from)

        if date_to:
            sql += " AND e.effective_date <= ?"
            params.append(date_to)

        sql += " ORDER BY d.document_number, e.edition_no"

        with self._connect() as conn:
            return conn.execute(sql, params).fetchall()

        def create_new_document(self, doc_no, doc_name, doc_type, source_file):

            today = datetime.date.today().isoformat()

            # 管理フォルダ作成
            doc_folder = os.path.join(self.base_dir, doc_no)
            os.makedirs(doc_folder, exist_ok=True)

            # 拡張子取得
            ext = os.path.splitext(source_file)[1]

            # 保存ファイル名
            new_filename = f"{doc_no}_v1{ext}"
            dest_path = os.path.join(doc_folder, new_filename)

            # コピー
            shutil.copy2(source_file, dest_path)

            # DB登録
            with self._connect() as conn:
                cur = conn.cursor()

                # Document_Master 登録
                cur.execute("""
                    INSERT INTO Document_Master (document_number, document_name, document_type)
                    VALUES (?, ?, ?)
                """, (doc_no, doc_name, doc_type))

                document_id = cur.lastrowid

                # Edition 登録（版1 修正中）
                cur.execute("""
                    INSERT INTO Document_Edition_Master
                    (document_id, edition_no, effective_date, edition_status, pdf_path)
                    VALUES (?, 1, ?, 1, ?)
                """, (document_id, today, dest_path))

                conn.commit()

    
        
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
    # 修正版の新規登録
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

    def create_revision(self, document_id: int, edition_no: int):

        with self._connect() as conn:
            cur = conn.cursor()

            # ① 元版取得
            cur.execute("""
                SELECT document_path
                FROM Document_Edition_Master
                WHERE document_id = ?
                  AND edition_no = ?
                  AND edition_status = ?
            """, (document_id, edition_no, self.LATEST))

            row = cur.fetchone()
            if not row:
                raise Exception("最新版が見つかりません")

            src_path = row[0]

            # ② 新版番号
            new_edition = edition_no + 1

            # ③ ファイルコピー
            base, ext = os.path.splitext(src_path)
            new_path = f"{base}_rev{new_edition}{ext}"
            shutil.copy2(src_path, new_path)

            # ④ 旧版を ARCHIVED
            cur.execute("""
                UPDATE Document_Edition_Master
                SET edition_status = ?
                WHERE document_id = ?
                  AND edition_status = ?
            """, (self.ARCHIVED, document_id, self.LATEST))

            # ⑤ 新版 INSERT
            cur.execute("""
                INSERT INTO Document_Edition_Master
                (document_id, edition_no, edition_status, document_path, effective_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                document_id,
                new_edition,
                self.DRAFT,
                new_path,
                datetime.date.today()
            ))


            # ⑥ Document_Correction_Master に登録
            cur.execute("""
                INSERT INTO Document_Correction_Master
                (document_number, edition_no, correction_path, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                document_id,
                new_edition,
                new_path,
                datetime.datetime.now()
            ))

    # ------------------------------------------------------------------
    # DB 接続（共通）
    # ------------------------------------------------------------------
    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)

        # ★ ここ！
        conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
