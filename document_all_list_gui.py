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

        columns = (
            "document_number",
            "document_name",
            "edition_no",
            "effective_date",
            "status",
            "pdf_path",
        )

        ysb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=ysb.set,
            selectmode="browse"
            )
        ysb.config(command=self.tree.yview)


        widths = {
            "document_number": 180,
            "document_name": 420,
            "edition_no": 80,
            "effective_date": 120,
            "status": 120,
            "pdf_path": 0,   # 非表示
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor=tk.W)

        # PDFパスは非表示
        self.tree.column("pdf_path", width=0, stretch=False)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        # 行色
        self.tree.tag_configure("latest", background="#E8F5E9")   # 薄緑
        self.tree.tag_configure("editing", background="#FFFDE7")  # 薄黄
        self.tree.tag_configure("old", background="#F5F5F5")      # 薄灰

    def _create_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="ファイルを開く", command=self._open_pdf)
        self.context_menu.add_command(label="修正版を作成", command=self.create_revision)

        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    def open_document(self):
        try:
            info = self._get_selected_ids()
        except Exception as e:
            messagebox.showwarning("注意", str(e))
            return

        # pdf_path は表示用 values から取得
        values = self.tree.item(self.tree.selection()[0], "values")
        pdf_path = values[5]

        if not os.path.exists(pdf_path):
            messagebox.showerror("エラー", "ファイルが見つかりません")
            return

        os.startfile(pdf_path)

    def _open_pdf(self):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        pdf_path = item["values"][-1]   # 最後の列が pdf_path

        if not pdf_path:
            messagebox.showwarning("警告", "PDFパスが登録されていません")
            return

        if not os.path.exists(pdf_path):
            messagebox.showerror("エラー", f"ファイルが存在しません\n{pdf_path}")
            return

        os.startfile(pdf_path)  # Windows


    def create_revision(self):
        try:
            info = self._get_selected_ids()
        except Exception as e:
            messagebox.showwarning("注意", str(e))
            return

        answer = messagebox.askyesno(
            "修正版作成",
            f"文書番号：{info['document_number']}\n"
            f"現行版：{info['edition_no']}\n\n"
            "修正版を作成しますか？"
        )

        if not answer:
            return

        try:
            self.db.create_revision(
                info["document_id"],
                info["edition_no"]
            )
        except Exception as e:
            messagebox.showerror("エラー", str(e))
            return

        messagebox.showinfo("完了", "修正版を作成しました")
        self._load_list()

    
    def _on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # ★ 右クリックした行を選択状態にする
        self.tree.selection_set(row_id)

        # メニュー表示
        self._popup_menu(event)

    def _popup_menu(self, event):
        menu = tk.Menu(self, tearoff=0)

        menu.add_command(
            label="文書を開く",
            command=self.open_document
        )

        menu.add_separator()

        menu.add_command(
            label="修正版を作成する",
            command=self.create_revision
        )

        menu.tk_popup(event.x_root, event.y_root)

    def _get_selected_ids(self):
        selected = self.tree.selection()
        if not selected:
            raise Exception("行が選択されていません")

        iid = selected[0]
        document_id, edition_no = map(int, iid.split(":"))

        values = self.tree.item(iid, "values")
        document_number = values[0]

        return {
            "document_id": document_id,
            "edition_no": edition_no,
            "document_number": document_number,
        }
   


    # --------------------------------------------------
    # 一覧ロード
    # --------------------------------------------------
    def _load_list(self):
        self.tree.delete(*self.tree.get_children())

        status_label = self.status_combo.get()
        status = self.STATUS_MAP.get(status_label)

        doc_no = self.doc_no_entry.get().strip()
        doc_name = self.doc_name_entry.get().strip()
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()

        rows = self.db.fetch_all_editions(
            status=status,
            document_number=self.doc_no_entry.get().strip(),
            document_name=self.doc_name_entry.get().strip(),
            date_from=self.date_from_entry.get().strip(),
            date_to=self.date_to_entry.get().strip(),
        )

        for row in rows:
            status_text = self.db.status_text(row["edition_status"])
            # ★ document_id + edition_no を iid に埋め込む
            iid = f'{row["document_id"]}:{row["edition_no"]}'

            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    row["document_number"],
                    row["document_name"],
                    row["edition_no"],
                    row["effective_date"],
                    status_text,
                    row["pdf_path"],
                )
            )


if __name__ == "__main__":
    app = DocumentAllListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
