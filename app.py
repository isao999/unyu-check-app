import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（丸伊運輸・実戦版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）", type="pdf")
csv_file = st.file_uploader("比較するCSV", type="csv")

if pdf_file and csv_file:
    st.info("解析中... PDFの数字とCSVを突き合わせています。")

    # 1. CSVの読み込み（時間を 1323 のような4桁形式に変換）
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        # CSVの「時間」が入っている列を探す（適宜列名を変えてね）
        # ここでは仮に「出発時間」という列名にしているよ
        time_col = df_csv.columns[0] # 一番左の列を時間と仮定
        df_csv['check_time'] = df_csv[time_col].astype(str).str.replace(':', '').str.zfill(4)
    except Exception as e:
        st.error(f"CSVエラー: {e}")

    # 2. PDFから数字を強引に抽出
    try:
        images = convert_from_bytes(pdf_file.read(), dpi=300)
        pdf_numbers = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="eng", config='--psm 11')
            # 3桁〜4桁の数字を全部拾う
            found = re.findall(r'\d{3,4}', text)
            pdf_numbers.extend([n.zfill(4) for n in found]) # 3桁は0を足して4桁に

        # 3. 照合（CSVの時間と、PDFで見つかった数字を比べる）
        st.subheader("照合結果")
        
        results = []
        for index, row in df_csv.iterrows():
            target = row['check_time']
            # PDFの中に、CSVの時間と同じ数字があるか？
            match = "⭕ 一致" if target in pdf_numbers else "❌ 不明"
            results.append({"元の時間": row[time_col], "判定": match})
        
        st.table(pd.DataFrame(results))
        
        with st.expander("PDFから見つかった全数字（確認用）"):
            st.write(list(set(pdf_numbers)))

    except Exception as e:
        st.error(f"PDF解析エラー: {e}")
