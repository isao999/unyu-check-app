import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（丸伊運輸・完全実戦版）")

# サイドバーに設定
st.sidebar.header("設定")
time_col_name = st.sidebar.text_input("CSVの時間列の名前", "出勤時間")
name_col_name = st.sidebar.text_input("CSVの名前列の名前", "氏名")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("出退勤CSVをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("解析中... 現場の『手書き』を根性で読み取っています。")

    # 1. CSVの読み込み（Shift-JIS/cp932対応）
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.success("CSVを読み込んだよ！")
    except Exception as e:
        st.error(f"CSVエラー: {e}")
        st.stop()

    # 2. PDFの解析（全テキストを抽出）
    try:
        images = convert_from_bytes(pdf_file.read(), dpi=300)
        full_text = ""
        for img in images:
            # 縦書き・横書き混在に強い設定(--psm 11)
            full_text += pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 11')
        
        # 改行や空白を整理
        full_text = re.sub(r'\s+', '', full_text)
    except Exception as e:
        st.error(f"PDF解析エラー: {e}")
        st.stop()

    # 3. 照合ロジック
    st.subheader("📋 照合結果の一覧")
    
    results = []
    for _, row in df_csv.iterrows():
        driver_name = str(row[name_col_name]).replace(" ", "").replace("　", "")
        csv_time = str(row[time_col_name]).replace(":", "")
        # 3桁〜4桁の数字に変換（例: 05:18 -> 0518 または 518）
        csv_time_short = str(int(csv_time)) if csv_time.isdigit() else csv_time

        # PDFの中に名前があるか？
        name_idx = full_text.find(driver_name)
        
        status = "❌ 不明"
        found_val = "見つからず"

        if name_idx != -1:
            # 名前の後ろ50文字以内にある数字を探す
            surrounding_text = full_text[name_idx : name_idx + 50]
            pdf_numbers = re.findall(r'\d{3,4}', surrounding_text)
            
            if csv_time_short in [str(int(n)) for n in pdf_numbers]:
                status = "✅ 一致"
                found_val = f"付近に {csv_time_short} を確認"
            else:
                found_val = f"名前はあったが時間は {pdf_numbers} のみ"
        
        results.append({
            "氏名": driver_name,
            "CSV時間": row[time_col_name],
            "判定": status,
            "備考": found_val
        })

    # 結果をテーブルで表示
    res_df = pd.DataFrame(results)
    st.table(res_df)

    # 補助的な確認用
    with st.expander("AIが読み取った全テキスト（文字化け確認用）"):
        st.text(full_text)
