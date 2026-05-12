import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（完全無料クラウド版）")

pdf_file = st.file_uploader("画像PDFをアップロード", type="pdf")
csv_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("完全無料のOCRで読み取り中...少し待ってね！")

    try:
        # PDFを画像にする
        images = convert_from_bytes(pdf_file.read())
        all_text = ""
        
        # 画像から文字を読み取る（Tesseractを使用）
        for img in images:
            text = pytesseract.image_to_string(img, lang="jpn")
            all_text += text
            
        st.subheader("PDFから見つかった時間")
        # 00:00 形式の時間を探す
        pdf_times = re.findall(r'\d{1,2}:\d{2}', all_text)
        
        if pdf_times:
            st.write(pdf_times)
        else:
            st.warning("時間が見つからなかったよ。画像がぼやけているかも？")

    except Exception as e:
        st.error(f"エラーが出たよ: {e}")

    # CSVの表示
    df_csv = pd.read_csv(csv_file)
    st.subheader("CSVのデータ")
    st.write(df_csv.head())
