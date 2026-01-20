import tkinter as tk
from tkinter import ttk
from document_info import DocumentInfo
import os
import subprocess
from tkinter import messagebox

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

        columns = ("文書番号", "文書名", "版", "発行日", "状態", "PDFパス")

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
            "状態": 120,
            "PDFパス": 0
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column("PDFパス", width=0, stretch=False)


        self.tree.pack(fill=tk.BOTH, expand=True)

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
            document_number = r[0]
            document_name = r[1]
            edition_no = r[2]
            effective_date = r[3]
            edition_status = r[4]
            pdf_path = r[5]

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
