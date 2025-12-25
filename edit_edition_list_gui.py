import tkinter as tk
from tkinter import ttk, messagebox
from document_info import DocumentInfo


class DraftEditionApprovalGUI(tk.Tk):
    """
    修正中版（edition_status=1）一覧表示 ＋ 承認 GUI
    """

    def __init__(self, db_path: str):
        super().__init__()
        self.title("修正中ドキュメント一覧（承認）")
        self.geometry("1050x600")

        self.db = DocumentInfo(db_path)

        self._create_widgets()
        self._load_draft_list()

    # ------------------------------------------------------------
    # GUI 構築
    # ------------------------------------------------------------
    def _create_widgets(self):

        # ---------- 操作フレーム ----------
        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)

        btn_refresh = tk.Button(
            ctrl_frame, text="再読込", width=12, command=self._load_draft_list
        )
        btn_refresh.pack(side=tk.LEFT)

        btn_approve = tk.Button(
            ctrl_frame, text="承認（最新版へ）", width=18,
            command=self._approve_selected
        )
        btn_approve.pack(side=tk.LEFT, padx=10)

        # ---------- 一覧 ----------
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = (
            "document_id",
            "document_number",
            "document_name",
            "edition_id",
            "edition_no",
            "effective_date",
            "status"
        )

        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=18
        )

        headings = {
            "document_id": "文書ID",
            "document_number": "文書番号",
            "document_name": "文書名",
            "edition_id": "版ID",
            "edition_no": "版",
            "effective_date": "発行日",
            "status": "状態"
        }

        widths = {
            "document_id": 80,
            "document_number": 150,
            "document_name": 300,
            "edition_id": 80,
            "edition_no": 80,
            "effective_date": 120,
            "status": 100
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------
    # 修正中版一覧取得
    # ------------------------------------------------------------
    def _load_draft_list(self):

        self.tree.delete(*self.tree.get_children())

        rows = self.db.fetch_editions_by_status(1)  # 修正中のみ

        for r in rows:
            status_text = self.db.status_text(r[6])

            self.tree.insert(
                "",
                tk.END,
                values=(
                    r[0],  # document_id
                    r[1],  # document_number
                    r[2],  # document_name
                    r[3],  # edition_id
                    r[4],  # edition_no
                    r[5],  # effective_date
                    status_text
                )
            )

    # ------------------------------------------------------------
    # 承認処理
    # ------------------------------------------------------------
    def _approve_selected(self):

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("確認", "承認する行を選択してください")
            return

        item = self.tree.item(selected[0])
        values = item["values"]

        document_id = values[0]
        edition_id = values[3]

        confirm = messagebox.askyesno(
            "承認確認",
            "選択した版を最新版として承認します。\nよろしいですか？"
        )

        if not confirm:
            return

        try:
            self.db.approve_edition(document_id, edition_id)
            messagebox.showinfo("完了", "最新版として承認しました")
            self._load_draft_list()

        except Exception as e:
            messagebox.showerror("エラー", f"承認に失敗しました\n{e}")


if __name__ == "__main__":
    app = DraftEditionApprovalGUI(r"C:\DataBase\document_master.db")
    app.mainloop()
