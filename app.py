import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageOps, ImageFilter
import re

st.title("運送業務・照合ツール（丸伊運輸・最終調整版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("CSVファイルをアップロード", type="csv")

if pdf_file and csv_file:
    st.info("画像を加工して、薄い文字をクッキリさせて読み取っているよ...")

    try:
        # DPIを300以上にして読み込み
        images = convert_from_bytes(pdf_file.read(), dpi=350)
        all_text = ""
        
        for img in images:
            # --- 画像処理：AIが読みやすいように加工 ---
            img = img.convert('L') # グレースケール（白黒）
            # 二値化（ある程度より薄い色は全部白、濃い色は全部黒にする）
            img = img.point(lambda x: 0 if x < 150 else 255) 
            
            # --- OCR実行：PSM 11 (文字をバラバラに探すモード) ---
            # 丸伊運輸さんの表形式には、6より11の方が効くことがあるよ
            custom_config = r'--psm 11 -l jpn+eng'
            text = pytesseract.image_to_string(img, config=custom_config)
            all_text += text
            
        st.subheader("PDFから見つかった時刻（候補）")
        
        # --- 修正版：もっと強引に数字を探す ---
        # 1. テキストから数字以外（記号や改行）を一度スペースに置き換える
        clean_text = re.sub(r'[^0-9]', ' ', all_text)
        # 2. 3桁または4桁の塊を全部抜き出す
        raw_numbers = re.findall(r'\b\d{3,4}\b', clean_text)
        
        times_list = []
        for num in raw_numbers:
            # 4桁の場合（1323など）
            if len(num) == 4:
                h, m = int(num[:2]), int(num[2:])
            # 3桁の場合（518など）
            else:
                h, m = int(num[:1]), int(num[1:])
            
            # 時刻としてあり得る数字だけを採用
            if h <= 23 and m <= 59:
                times_list.append(f"{h:02d}:{m:02d}")
        
        # 重複を消して、時間順に並べる
        final_times = sorted(list(set(times_list)))

        if final_times:
            st.success(f"{len(final_times)}件の候補を見つけたよ！")
            st.write(final_times)
        else:
            st.warning("やっぱり見つからない...画像が薄すぎるかも？")

        with st.expander("AIが「加工後」に読み取った文字を確認"):
            st.text(all_text)

    except Exception as e:
        st.error(f"エラー: {e}")

    # CSV読み込み
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.subheader("CSVのデータ（照合用）")
        st.write(df_csv.head())
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
