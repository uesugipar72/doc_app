import tkinter as tk
from tkinter import ttk
from document_info import DocumentInfo
import os
import subprocess
from tkinter import messagebox
import datetime

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
        self._create_context_menu()
        self._load_list()

    # --------------------------------------------------
    # GUI
    # --------------------------------------------------
    def _create_widgets(self):

        # ===== 検索条件 =====
        cond_frame = tk.LabelFrame(self, text="抽出条件")
        cond_frame.pack(fill=tk.X, padx=10, pady=5)

        # --- 表示区分 ---
        tk.Label(cond_frame, text="表示区分").grid(row=0, column=0, padx=5, pady=2)
        self.status_combo = ttk.Combobox(
            cond_frame,
            values=list(self.STATUS_MAP.keys()),
            state="readonly",
            width=12
        )
        self.status_combo.set("すべて")
        self.status_combo.grid(row=0, column=1, padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self._load_list())

        # --- 文書番号 ---
        tk.Label(cond_frame, text="文書番号").grid(row=0, column=2, padx=5)
        self.doc_no_entry = tk.Entry(cond_frame, width=20)
        self.doc_no_entry.grid(row=0, column=3, padx=5)

        # --- 文書名 ---
        tk.Label(cond_frame, text="文書名").grid(row=0, column=4, padx=5)
        self.doc_name_entry = tk.Entry(cond_frame, width=30)
        self.doc_name_entry.grid(row=0, column=5, padx=5)

        # --- 作成日範囲 ---
        tk.Label(cond_frame, text="発行日 From").grid(row=1, column=0, padx=5)
        self.date_from_entry = tk.Entry(cond_frame, width=12)
        self.date_from_entry.grid(row=1, column=1, padx=5)

        tk.Label(cond_frame, text="To").grid(row=1, column=2, padx=5)
        self.date_to_entry = tk.Entry(cond_frame, width=12)
        self.date_to_entry.grid(row=1, column=3, padx=5)

        tk.Label(cond_frame, text="(YYYY-MM-DD)").grid(row=1, column=4, padx=5)

        # --- 検索ボタン ---
        tk.Button(cond_frame, text="再表示", command=self._load_list)\
            .grid(row=1, column=5, padx=10)


        # ===== 一覧 =====
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("文書番号", "文書名", "版", "発行日", "状態", "PDFパス")

        # ★ スクロールバー作成
        ysb = ttk.Scrollbar(list_frame, orient="vertical")

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=20,
            yscrollcommand=ysb.set
        )
        ysb.config(command=self.tree.yview)


        widths = {
            "文書番号": 180,
            "文書名": 420,
            "版": 80,
            "発行日": 120,
            "状態": 120,
            "PDFパス": 0
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor=tk.W)

        # PDFパスは非表示
        self.tree.column("PDFパス", width=0, stretch=False)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        # 行色
        self.tree.tag_configure("latest", background="#E8F5E9")   # 薄緑
        self.tree.tag_configure("editing", background="#FFFDE7")  # 薄黄
        self.tree.tag_configure("old", background="#F5F5F5")      # 薄灰



    def _create_context_menu(self):
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="文書を開く", command=self.open_document)
        self.menu.add_separator()
        self.menu.add_command(label="修正版を作成する", command=self.create_revision)

        self.tree.bind("<Button-3>", self._show_context_menu)


    def _show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.menu.post(event.x_root, event.y_root)

    def open_document(self):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        pdf_path = values[5]   # PDFパス列

        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("エラー", f"ファイルが存在しません\n{pdf_path}")
            return

        try:
            os.startfile(pdf_path)
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    def create_revision(self):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")

        document_number = values[0]
        edition_no = values[2]

        answer = messagebox.askyesno(
            "修正版作成",
            f"文書番号：{document_number}\n"
            f"現行版：{edition_no}\n\n"
            "修正版を作成しますか？"
        )

        if not answer:
            return

        # ★ ここで DB に DRAFT 版を作成する処理を呼ぶ
        # self.db.create_revision(...)

        messagebox.showinfo("完了", "修正版を作成しました")
        self._load_list()

    def parse_date(self, date_str):
        """
        YYYY-MM-DD 形式の日付文字列を date に変換
        失敗したら None を返す
        """
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None


    # --------------------------------------------------
    # 一覧ロード
    # --------------------------------------------------
    def _load_list(self):

        doc_no_cond = self.doc_no_entry.get().strip()
        doc_name_cond = self.doc_name_entry.get().strip()
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()

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
            document_number = r[0]
            document_name = r[1]
            edition_no = r[2]
            effective_date = r[3]
            edition_status = r[4]
            pdf_path = r[5]

            # --- 文書番号 ---
            if doc_no_cond and doc_no_cond not in document_number:
                continue

            # --- 文書名 ---
            if doc_name_cond and doc_name_cond not in document_name:
                continue

            # --- 発行日範囲 ---
            doc_date = self.parse_date(effective_date)
            from_date = self.parse_date(date_from)
            to_date = self.parse_date(date_to)

            if doc_date:
                if from_date and doc_date < from_date:
                    continue
                if to_date and doc_date > to_date:
                    continue

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
                    status_text,
                    pdf_path
                ),
                tags=(tag,)
            )


    

if __name__ == "__main__":
    app = DocumentAllListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
