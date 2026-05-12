import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（完全無料クラウド版）")

pdf_file = st.file_uploader("画像PDFをアップロード", type="pdf")
csv_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("読み取り中...（精度を上げて読み込んでいるよ）")

    try:
        # --- 1. PDFを画像にする（DPIを300に上げて精度をアップ！） ---
        images = convert_from_bytes(pdf_file.read(), dpi=300)
        all_text = ""
        
        for img in images:
            # 日本語と英語の両方で読み取り
            text = pytesseract.image_to_string(img, lang="jpn+eng")
            all_text += text
            
        st.subheader("PDFから見つかった時間")
        # 00:00 形式の時間を探す（半角・全角両方対応できるよう工夫）
        pdf_times = re.findall(r'\d{1,2}[:：]\d{2}', all_text)
        
        if pdf_times:
            # 全角のコロンを半角に直して表示
            clean_times = [t.replace('：', ':') for t in pdf_times]
            st.write(clean_times)
        else:
            st.warning("時間が見つからなかったよ。OCRの読み取り結果を確認してみて。")
            with st.expander("OCRが読み取った生のテキストを見る"):
                st.text(all_text)

    except Exception as e:
        st.error(f"PDFエラー: {e}")

    # --- 2. CSVの読み込み（Shift-JIS対策！） ---
    try:
        # 日本語WindowsのCSVは 'cp932' (Shift-JIS) を指定するのがコツ！
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.subheader("CSVのデータ")
        st.write(df_csv.head())
    except UnicodeDecodeError:
        # もし cp932 でもダメなら utf-8 でリトライ
        csv_file.seek(0)
        df_csv = pd.read_csv(csv_file, encoding='utf-8')
        st.write(df_csv.head())
    except Exception as e:
        st.error(f"CSVエラー: {e}")
