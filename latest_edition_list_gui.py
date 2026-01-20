import tkinter as tk
from tkinter import ttk
from master_data_fetcher_document import MasterDataFetcherDocument


class LatestEditionListGUI(tk.Tk):
    """
    最新版ドキュメント一覧 GUI
    ・最新版保証：edition_status = 0
    ・Document × Edition JOIN 結果のみ表示
    """

    def __init__(self, db_name: str):
        super().__init__()
        self.title("最新版ドキュメント一覧")
        self.geometry("1100x650")

        self.db = MasterDataFetcherDocument(db_name)

        self._create_widgets()
        self._load_latest_list()

    # ------------------------------------------------------------------
    # GUI 構築
    # ------------------------------------------------------------------
    def _create_widgets(self):

        # ========= 検索条件 =========
        cond_frame = tk.LabelFrame(self, text="検索条件", padx=10, pady=10)
        cond_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cond_frame, text="文書名").grid(row=0, column=0, sticky="e")
        self.entry_docname = tk.Entry(cond_frame, width=30)
        self.entry_docname.grid(row=0, column=1, padx=5)

        btn_search = tk.Button(
            cond_frame, text="検索", command=self._load_latest_list
        )
        btn_search.grid(row=0, column=2, padx=10)

        # ========= 一覧 =========
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = (
            "文書番号",
            "文書名",
            "版",
            "発行日",
            "状態",
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=20
        )

        # 列設定
        self.tree.heading("文書番号", text="文書番号")
        self.tree.column("文書番号", width=160, anchor="w")

        self.tree.heading("文書名", text="文書名")
        self.tree.column("文書名", width=380, anchor="w")

        self.tree.heading("版", text="版")
        self.tree.column("版", width=60, anchor="center")

        self.tree.heading("発行日", text="発行日")
        self.tree.column("発行日", width=120, anchor="center")

        self.tree.heading("状態", text="状態")
        self.tree.column("状態", width=100, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 行色（最新版は薄緑）
        self.tree.tag_configure("latest", background="#E8F5E9")

    # ------------------------------------------------------------------
    # 最新版一覧ロード
    # ------------------------------------------------------------------
    def _load_latest_list(self):

        keyword = self.entry_docname.get().strip()

        # 一覧クリア
        for row in self.tree.get_children():
            self.tree.delete(row)

        # 最新版取得（SQL保証）
        rows = self.db.fetch_latest_documents()

        for r in rows:
            (
                document_id,
                document_number,
                document_name,
                edition_id,
                edition_no,
                effective_date,
                edition_status,
            ) = r

            # 文書名フィルタ（部分一致）
            if keyword and keyword not in document_name:
                continue

            self.tree.insert(
                "",
                tk.END,
                values=(
                    document_number,
                    document_name,
                    edition_no,
                    effective_date,
                    "最新",
                ),
                tags=("latest",)
            )


if __name__ == "__main__":
    app = LatestEditionListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
