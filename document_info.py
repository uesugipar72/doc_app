import tkinter as tk
from tkinter import ttk, messagebox
from master_data_fetcher_document import MasterDataFetcherDocument


class LatestEditionListGUI(tk.Tk):
    """
    最新版（active document の最新版）を一覧表示する GUI
    equipment_info の構成を参考にして作成
    """
    def __init__(self, db_name="document_master.db"):
        super().__init__()
        self.title("最新版ドキュメント一覧")
        self.geometry("1100x650")

        self.db = MasterDataFetcherDocument(db_name)

        self._create_widgets()
        self._load_latest_list()

    # ----------------------------------------------------------------------
    # GUI 構築
    # ----------------------------------------------------------------------
    def _create_widgets(self):

        # ---------- 検索条件フレーム ----------
        cond_frame = tk.LabelFrame(self, text="検索条件", padx=10, pady=10)
        cond_frame.pack(fill=tk.X, padx=10, pady=5)

        # 文書名 (部分一致)
        tk.Label(cond_frame, text="文書名").grid(row=0, column=0, sticky="e")
        self.entry_docname = tk.Entry(cond_frame, width=30)
        self.entry_docname.grid(row=0, column=1, padx=5)

        # ステータス
        tk.Label(cond_frame, text="ステータス").grid(row=0, column=2, sticky="e")
        self.combo_status = ttk.Combobox(
            cond_frame, width=15, values=["active", "inactive", "all"], state="readonly")
        self.combo_status.current(0)
        self.combo_status.grid(row=0, column=3, padx=5)

        # 検索ボタン
        btn_search = tk.Button(cond_frame, text="検索", command=self._load_latest_list)
        btn_search.grid(row=0, column=4, padx=10)

        # ---------- 一覧フレーム ----------
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = [
            "document_id", "document_name",
            "edition_no", "edition_code",
            "effective_date", "usege_status"
        ]

        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.pack(fill=tk.BOTH, expand=True)

    # ----------------------------------------------------------------------
    # 最新版一覧を取得して表示
    # ----------------------------------------------------------------------
    def _load_latest_list(self):

        # 検索条件取得
        name_keyword = self.entry_docname.get().strip()
        status_filter = self.combo_status.get()

        # 一覧クリア
        for row in self.tree.get_children():
            self.tree.delete(row)

        # active documents を取得
        doc_conditions = {}
        if status_filter != "all":
            if status_filter == "active":
                doc_conditions["usege_status"] = 1
            elif status_filter == "inactive":
                doc_conditions["usege_status"] = 0

        doc_rows = (
            self.db.fetch_by_conditions("Document_Master", doc_conditions)
            if doc_conditions
            else self.db.fetch_all("Document_Master")
            )

        # 文書名フィルタ（部分一致）
        if name_keyword:
            doc_rows = [r for r in doc_rows if name_keyword in str(r[2])]

        for doc in doc_rows:
            document_id = doc[0]
            document_name = doc[2]

            # 最新版取得
            latest = self._fetch_latest_edition(document_id)
            if latest is None:
                continue

            # edition_master のカラム指定例
            edition_no = latest[2]
            edition_code = latest[3]
            effective_date = latest[6]
            edition_status = latest[8]

            # 一覧へ追加
            usege_status_value = doc[8]  # ← usege_status のインデックス
            usege_status_text = "active" if usege_status_value == 1 else "inactive"
            self.tree.insert(
                "", tk.END,
                values=(
                    document_id,
                    document_name,
                    edition_no,
                    edition_code,
                    effective_date,
                    usege_status_text
                )
            )

    # ----------------------------------------------------------------------
    # 指定 document_id の最新版（edition_no 最大）を取得
    # ----------------------------------------------------------------------
    def _fetch_latest_edition(self, document_id):

        rows = self.db.fetch_by_conditions(
            "Document_Edition_Master",
            {"document_id": document_id}
        )

        if not rows:
            return None

        # edition_no 最大のものが最新版
        latest = max(rows, key=lambda r: r[2])

        return latest


if __name__ == "__main__":
    app = LatestEditionListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
