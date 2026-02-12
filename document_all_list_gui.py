import tkinter as tk
from tkinter import ttk
from document_info import DocumentInfo
import os
import subprocess
from tkinter import messagebox
from tkinter import filedialog
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

    def __init__(self, db_path: str, base_dir: str):
        super().__init__()
        self.title("ドキュメント一覧")
        self.geometry("1100x650")

        self.db = DocumentInfo(db_path, base_dir)

        self._create_widgets()
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
        # --- 新規文書登録ボタン ---
        tk.Button(cond_frame, text="新規文書登録", command=self._open_new_document_dialog)\
            .grid(row=1, column=6, padx=10)    

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

        # 表示名マップ
        COLUMN_LABELS = {
            "document_number": "文書番号",
            "document_name": "文書名",
            "edition_no": "版",
            "effective_date": "発行日",
            "status": "状態",
            "pdf_path": "PDFパス",
        }

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
            self.tree.heading(col, text=COLUMN_LABELS[col])
            self.tree.column(col, width=widths[col], anchor=tk.W)

        # PDFパスは非表示
        self.tree.column("pdf_path", width=0, stretch=False)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        self._create_context_menu()

        # 行色
        self.tree.tag_configure("latest", background="#E8F5E9")   # 薄緑
        self.tree.tag_configure("editing", background="#FFFDE7")  # 薄黄
        self.tree.tag_configure("old", background="#F5F5F5")      # 薄灰

    def _open_new_document_dialog(self):
        dialog = NewDocumentDialog(self, self.db, self._load_list)
        dialog.grab_set()
        # --------------------------------------------------    

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
            # 行色タグ判定
            if row["edition_status"] == 0:
                tag = "latest"
            elif row["edition_status"] == 1:
                tag = "editing"
            else:
                tag = "old"

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
                ),
                tags=(tag,) # 行色タグ
            )
class NewDocumentDialog(tk.Toplevel):

    def __init__(self, master, db: DocumentInfo, refresh_callback):
        super().__init__(master)
        self.db = db
        self.refresh_callback = refresh_callback

        self.title("新規文書登録")
        self.geometry("420x260")
        self.resizable(False, False)

        self._create_widgets()

    def _create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # ===== 文書区分 =====
        tk.Label(frame, text="文書区分").grid(row=0, column=0, sticky="e", pady=5)
        self.category_combo = ttk.Combobox(
            frame,
            values=["RE", "CO", "EM", "EX"],
            state="readonly",
            width=27
        )
        self.category_combo.grid(row=0, column=1, pady=5)
        self.category_combo.bind("<<ComboboxSelected>>", self._update_doc_no)

        # ===== 部門 =====
        tk.Label(frame, text="部門").grid(row=1, column=0, sticky="e", pady=5)
        self.department_combo = ttk.Combobox(
            frame,
            values=["病理", "生理", "検体", "細菌"],
            state="readonly",
            width=27
        )
        self.department_combo.grid(row=1, column=1, pady=5)
        self.department_combo.bind("<<ComboboxSelected>>", self._update_doc_no)

        # ===== 文書番号（自動生成）=====
        tk.Label(frame, text="文書番号").grid(row=2, column=0, sticky="e", pady=5)
        self.doc_no_var = tk.StringVar()
        self.doc_no_entry = tk.Entry(
            frame,
            textvariable=self.doc_no_var,
            state="readonly",
            width=30
        )
        self.doc_no_entry.grid(row=2, column=1, pady=5)

        # ===== 文書名 =====
        tk.Label(frame, text="文書名").grid(row=3, column=0, sticky="e", pady=5)
        self.doc_name_entry = tk.Entry(frame, width=30)
        self.doc_name_entry.grid(row=3, column=1, pady=5)

        # ===== 文書種別 =====
        tk.Label(frame, text="ファイル種別").grid(row=4, column=0, sticky="e", pady=5)
        self.type_combo = ttk.Combobox(
            frame,
            values=["Word", "Excel", "PowerPoint"],
            state="readonly",
            width=27
        )
        self.type_combo.set("Word")
        self.type_combo.grid(row=4, column=1, pady=5)

        # ===== ボタン =====
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        tk.Button(btn_frame, text="登録", width=10,
                    command=self._register_document).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="キャンセル", width=10,
                    command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _update_doc_no(self, event=None):

        category = self.category_combo.get()
        department = self.department_combo.get()

        if not category or not department:
            return

        # DBから最大番号取得
        next_no = self.db.get_next_document_number(category, department)

        doc_no = f"{category}-{department}-{next_no:04d}"

        self.doc_no_var.set(doc_no)



    def _register_document(self,event=None):
        doc_no = self.doc_no_entry.get().strip()
        doc_name = self.doc_name_entry.get().strip()
        doc_type = self.type_combo.get()

        if not doc_no or not doc_name:
            messagebox.showwarning("入力エラー", "文書番号と文書名は必須です")
            return

        # ===== ファイル選択 =====
        source_path = filedialog.askopenfilename(
            title="登録するファイルを選択",
            initialdir=os.path.expanduser("~/Documents"),
            filetypes=[
                ("Word", "*.docx"),
                ("Excel", "*.xlsx"),
                ("PowerPoint", "*.pptx"),
                ("すべてのファイル", "*.*")
            ]
        )

        if not source_path:
            return

        try:
            # DB登録＆コピー
            saved_path = self.db.create_new_document(
                doc_no,
                doc_name,
                doc_type,
                source_path
            )
        except Exception as e:
            messagebox.showerror("エラー", str(e))
            return

        messagebox.showinfo("完了", "新規文書を登録しました")

        # 一覧更新
        self.refresh_callback()

        # ★ 登録した文書を自動で開く
        os.startfile(saved_path)

        self.destroy()



if __name__ == "__main__":
    app = DocumentAllListGUI(
        db_path=r"C:\DataBase\document_master.db",
        base_dir=r"C:\DocumentSystemOriginFile"
    )
    app.mainloop()
