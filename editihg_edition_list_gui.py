import tkinter as tk
from tkinter import ttk, messagebox
from document_info import DocumentInfo



class EditingEditionListGUI(tk.Tk):
    """
    修正中版一覧 ＋ 承認（最新版切替）GUI
    ・修正中：edition_status = 1
    ・承認処理は DB 側に委譲
    """

    def __init__(self, db_name: str):
        super().__init__()
        self.title("修正中ドキュメント一覧（承認）")
        self.geometry("1150x650")

        self.db = DocumentInfo(db_name)

        self._create_widgets()
        self._load_editing_list()

    # ------------------------------------------------------------------
    # GUI 構築
    # ------------------------------------------------------------------
    def _create_widgets(self):

        # ========= 上部 =========
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        btn_refresh = tk.Button(
            top_frame, text="再読込", command=self._load_editing_list
        )
        btn_refresh.pack(side=tk.LEFT)

        btn_approve = tk.Button(
            top_frame,
            text="承認して最新版にする",
            bg="#4CAF50",
            fg="white",
            command=self._approve_selected
        )
        btn_approve.pack(side=tk.RIGHT)

        # ========= 一覧 =========
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = (
            "文書番号",
            "文書名",
            "版",
            "修正日",
            "状態",
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=20,
            selectmode="browse"
        )

        self.tree.heading("文書番号", text="文書番号")
        self.tree.column("文書番号", width=160)

        self.tree.heading("文書名", text="文書名")
        self.tree.column("文書名", width=420)

        self.tree.heading("版", text="版")
        self.tree.column("版", width=60, anchor="center")

        self.tree.heading("修正日", text="修正日")
        self.tree.column("修正日", width=120, anchor="center")

        self.tree.heading("状態", text="状態")
        self.tree.column("状態", width=120, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 修正中は薄黄
        self.tree.tag_configure("editing", background="#FFFDE7")

    # ------------------------------------------------------------------
    # 修正中一覧ロード
    # ------------------------------------------------------------------
    def _load_editing_list(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.db.fetch_editing_documents()  # edition_status = 1

        for r in rows:
            (
                document_id,
                document_number,
                document_name,
                edition_id,
                edition_no,
                update_date,
                edition_status,
            ) = r

            self.tree.insert(
                "",
                tk.END,
                iid=str(edition_id),  # ← 承認処理で使う
                values=(
                    document_number,
                    document_name,
                    edition_no,
                    update_date,
                    "修正中",
                ),
                tags=("editing",)
            )

    # ------------------------------------------------------------------
    # 承認処理
    # ------------------------------------------------------------------
    def _approve_selected(self):

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("確認", "承認する修正中版を選択してください。")
            return

        edition_id = int(selected[0])

        if not messagebox.askyesno(
            "承認確認",
            "選択した修正中版を最新版として承認します。\nよろしいですか？"
        ):
            return

        try:
            self.db.approve_edition(edition_id)
            messagebox.showinfo("完了", "最新版として承認しました。")
            self._load_editing_list()
        except Exception as e:
            messagebox.showerror("エラー", str(e))


if __name__ == "__main__":
    app = EditingEditionListGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
