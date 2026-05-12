import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageOps
import re

st.title("運送業務・照合ツール（丸伊運輸・高精度版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("解析中... 記号に埋もれた数字を探しています。")

    try:
        images = convert_from_bytes(pdf_file.read(), dpi=300)
        all_text = ""
        
        for img in images:
            img = img.convert('L') # 白黒
            img = ImageOps.autocontrast(img) # コントラスト強調
            # 表形式に強い設定で読み込み
            text = pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 6')
            all_text += text
            
        st.subheader("PDFから見つかった時刻（候補）")
        
        # --- 修正版：時刻探しのロジック ---
        # 1. まず「数字以外のゴミ」を適度に無視して、数字の塊を探す
        # 2. 3桁または4桁の数字をすべて抜き出す
        raw_numbers = re.findall(r'\d{3,4}', all_text)
        
        times_list = []
        for num in raw_numbers:
            # 4桁の場合（例：1323）
            if len(num) == 4:
                hour = int(num[:2])
                minute = int(num[2:])
            # 3桁の場合（例：856 → 08:56）
            elif len(num) == 3:
                hour = int(num[:1])
                minute = int(num[1:])
            
            # 時刻として妥当か（0〜23時、0〜59分）チェック
            if hour <= 23 and minute <= 59:
                # 446（4時46分）なども拾うため、念のためリストに追加
                times_list.append(f"{hour:02d}:{minute:02d}")
        
        # 重複を消して、見やすく並べ替え
        final_times = sorted(list(set(times_list)))

        if final_times:
            st.success(f"{len(final_times)}件の時刻候補が見つかったよ！")
            st.write(final_times)
        else:
            st.warning("時刻が見つからなかったよ。")

        with st.expander("AIが読み取った生のテキスト（ここをチェック！）"):
            st.text(all_text)

    except Exception as e:
        st.error(f"解析エラー: {e}")

    # CSV読み込み
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.subheader("CSVのデータ（照合対象）")
        st.write(df_csv.head())
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
