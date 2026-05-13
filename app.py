import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（丸伊運輸・決戦版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("出退勤CSVをアップロード", type="csv")

if pdf_file and csv_file:
    # 1. CSVの読み込み
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.success("CSV読み込み完了！")
    except Exception as e:
        st.error(f"CSVエラー: {e}")
        st.stop()

    # サイドバーで列を選択
    st.sidebar.header("CSV設定")
    cols = df_csv.columns.tolist()
    name_col = st.sidebar.selectbox("氏名", cols)
    in_time_col = st.sidebar.selectbox("出勤時間", cols)
    out_time_col = st.sidebar.selectbox("退勤時間", cols)

    if st.button("出退勤を一括照合！"):
        st.info("解析中... 文字の泥沼から数字を掘り出しています。")

        # 2. PDFの解析（精度重視）
        try:
            images = convert_from_bytes(pdf_file.read(), dpi=300)
            full_text = ""
            for img in images:
                # 枠線に邪魔されても文字を拾う設定
                full_text += pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 11')
            
            # 検索しやすいように改行をスペースに置換
            full_text = full_text.replace('\n', ' ')
        except Exception as e:
            st.error(f"PDF解析エラー: {e}")
            st.stop()

        # 3. 照合
        results = []
        for _, row in df_csv.iterrows():
            name = str(row[name_col]).replace(" ", "").replace("　", "")
            # 名前が認識しにくい場合のため、先頭2文字でも探す
            short_name = name[:2]
            
            def to_num(t):
                s = re.sub(r'\D', '', str(t))
                return str(int(s)) if s else None

            target_in = to_num(row[in_time_col])
            target_out = to_num(row[out_time_col])

            # PDFから名前を探す
            match = re.search(short_name, full_text)
            
            status_in, status_out = "❌", "❌"
            found_nums = []

            if match:
                # 名前の前後200文字をチェック（出退勤の両方が入る範囲）
                start = max(0, match.start() - 50)
                end = min(len(full_text), match.end() + 200)
                search_area = full_text[start:end]
                
                # 数字をすべて抽出
                found_nums = re.findall(r'\d+', search_area)
                
                # 「0.0001323」のような塊を分解してチェック
                all_possible_nums = []
                for n in found_nums:
                    all_possible_nums.append(n)
                    if len(n) > 4: # 長い数字は後ろ4桁や3桁も候補にする
                        all_possible_nums.append(n[-4:])
                        all_possible_nums.append(str(int(n[-4:])) if n[-4:].isdigit() else "")

                if target_in and any(target_in in n for n in all_possible_nums): status_in = "✅"
                if target_out and any(target_out in n for n in all_possible_nums): status_out = "✅"

            results.append({
                "氏名": name,
                "出勤(CSV)": row[in_time_col], "出勤": status_in,
                "退勤(CSV)": row[out_time_col], "退勤": status_out,
                "付近の数字": list(set(found_nums))[:5] # 確認用に一部表示
            })

        st.table(pd.DataFrame(results))
        with st.expander("AIが読み取った全テキスト"):
            st.text(full_text)
