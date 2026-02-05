import pandas as pd
import re

# ===== 入出力設定 =====
INPUT_EXCEL = "細胞.xlsx"
SHEET_NAME = "Sheet1"
OUTPUT_EXCEL = "細胞_材料分割.xlsx"
OUTPUT_CSV = "細胞_材料分割.csv"

# ===== Excel読み込み（見出し行を指定）=====
# 見出しが3行目にあるため header=2
df = pd.read_excel(INPUT_EXCEL, sheet_name=SHEET_NAME, header=2)

# 列名を明示的に設定（必要に応じて調整）
df.columns = [
    "標本番号",
    "採取日時",
    "受付日時",
    "診療科",
    "材料",
    "部位",
    "切除/採取方法",
    "診療報酬"
]

# ===== 材料列の改行を分割 =====
def split_material(text):
    if pd.isna(text):
        return []
    # Excel由来の改行コードに対応
    parts = re.split(r"_x000D_|\r\n|\n", str(text))
    return [p.strip() for p in parts if p.strip()]

df["材料_list"] = df["材料"].apply(split_material)

# ===== 行展開 =====
df_out = df.explode("材料_list").copy()
df_out = df_out.drop(columns=["材料"])
df_out = df_out.rename(columns={"材料_list": "材料"})

# ===== 見出し行の混入を除外（念のため）=====
df_out = df_out[df_out["標本番号"] != "標本番号"]

# ===== 出力 =====
df_out.to_excel(OUTPUT_EXCEL, index=False)
df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print("完了しました")



