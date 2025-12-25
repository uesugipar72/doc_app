import tkinter as tk
from tkinter import ttk
from document_info import DocumentInfo


class DocumentAllListGUI(tk.Tk):
    """
    全ドキュメント（Edition単位）一覧
    ・最新版 / 修正中 / 廃棄 をコンボで抽出
    """

    STATUS_MAP = {
        "最新版": 0,
        "修正中": 1,
        "廃棄文書": 9,
        "すべて": None
    }

    def __init__(self, db_path: str):
        super().__init__()
        self.title("ドキュメント一覧")
        self.geometry("1100x650")

        self.db = DocumentInfo(db_path)

        self._create_widgets()
        self._load_list()

    # --------------------------------------------------
    # GUI
    # --------------------------------------------------
    def _create_widgets(self):

        # ===== 検索条件 =====
        cond_frame = tk.LabelFrame(self, text="抽出条件")
        cond_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cond_frame, text="表示区分").pack(side=tk.LEFT, padx=5)

        self.status_combo = ttk.Combobox(
            cond_frame,
            values=list(self.STATUS_MAP.keys()),
            state="readonly",
            width=15
        )
        self.status_combo.set("すべて")
        self.status_combo.pack(side=tk.LEFT, padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self._load_list())

        # ===== 一覧 =====
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("文書番号", "文書名", "版", "発行日", "状態")

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=20
        )

        widths = {
            "文書番号": 180,
            "文書名": 420,
            "版": 80,
            "発行日": 120,
            "状態": 120
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 行色
        self.tree.tag_configure("latest", background="#E8F5E9")   # 薄緑
        self.tree.tag_configure("editing", background="#FFFDE7")  # 薄黄
        self.tree.tag_configure("old", background="#F5F5F5")      # 薄灰

    # --------------------------------------------------
    # 一覧ロード
    # --------------------------------------------------
    def _load_list(self):

        self.tree.delete(*self.tree.get_children())

        selected = self.status_combo.get()
        status = self.STATUS_MAP[selected]

        if status is None:
            rows = self.db.fetch_all_editions()
        elif status == 0:
            rows = self.db.fetch_latest_documents()
        else:
            rows = self.db.fetch_editions_by_status(status)

        for r in rows:
            # fetch_latest_documents と fetch_all_editions の差を吸収
            document_number = r[1]
            document_name = r[2]
            edition_no = r[3]
            effective_date = r[4]
            edition_status = r[5]

            status_text = self.db.status_text(edition_status)

            tag = (
                "latest" if edition_status == 0
                else "editing" if edition_status == 1
                else "old"
            )

            self.tree.insert(
                "",
                tk.END,
                values=(
                    document_number,
                    document_name,
                    edition_no,
                    effective_date,
                    status_text
                ),
                tags=(tag,)
            )


if __name__ == "__main__":
    app = DocumentAllListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
