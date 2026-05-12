import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageOps
import re

st.title("運送業務・照合ツール（丸伊運輸・専用版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("解析中... 4桁の数字から『時刻』を探しています。")

    try:
        images = convert_from_bytes(pdf_file.read(), dpi=300)
        all_text = ""
        
        for img in images:
            img = img.convert('L')
            img = ImageOps.autocontrast(img)
            # OCR実行
            text = pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 6')
            all_text += text
            
        st.subheader("PDFから抽出した時刻（推測）")
        
        # 【ここが重要！】4桁の数字（0000〜2359）を探すルール
        # 12:34 形式だけでなく、1234 のような4桁も探す
        found_patterns = re.findall(r'\b([012][0-9][:：\s\.]?[0-5][0-9])\b', all_text)
        
        if found_patterns:
            # 記号を消して「12:34」の形に整える
            times_list = []
            for t in found_patterns:
                clean_t = re.sub(r'[:：\s\.]', '', t)
                if len(clean_t) == 4:
                    # 時刻として妥当か（時が23以下、分が59以下）チェック
                    hour = int(clean_t[:2])
                    minute = int(clean_t[2:])
                    if hour <= 23 and minute <= 59:
                        times_list.append(f"{clean_t[:2]}:{clean_t[2:]}")
            
            # 重複を排除して表示
            final_times = sorted(list(set(times_list)))
            st.write(final_times)
        else:
            st.warning("時刻が見つかりませんでした。")
            
        with st.expander("AIが読み取った生のテキスト（確認用）"):
            st.text(all_text)

    except Exception as e:
        st.error(f"解析エラー: {e}")

    # CSV読み込み（文字コード対策済み）
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.subheader("CSVのデータ")
        st.write(df_csv.head())
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
