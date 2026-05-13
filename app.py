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
        st.success("CSV読み込みOK！")
    except Exception as e:
        st.error(f"CSVエラー: {e}")
        st.stop()

    # サイドバーで列を選択
    st.sidebar.header("CSVの列設定")
    cols = df_csv.columns.tolist()
    name_col = st.sidebar.selectbox("氏名の列", cols)
    in_time_col = st.sidebar.selectbox("「出勤」時間の列", cols)
    out_time_col = st.sidebar.selectbox("「退勤」時間の列", cols)

    if st.button("出退勤をまとめて照合！"):
        st.info("解析中... 記号の山から数字を掘り出しています。")

        # 2. PDFの解析（精度重視）
        try:
            images = convert_from_bytes(pdf_file.read(), dpi=300)
            full_text = ""
            for img in images:
                # 枠線に強い設定(PSM 11)
                full_text += pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 11')
        except Exception as e:
            st.error(f"PDF解析エラー: {e}")
            st.stop()

        # 3. 照合ロジック
        results = []
        for _, row in df_csv.iterrows():
            raw_name = str(row[name_col])
            # 氏名の最初の2文字で探す（手書きだとフルネーム認識が難しいため）
            short_name = raw_name.replace(" ", "").replace("　", "")[:2]
            
            # 時間を「数字だけ」にする関数（例: 05:18 -> 518）
            def get_time_val(t):
                s = re.sub(r'\D', '', str(t))
                return str(int(s)) if s and s.isdigit() else None

            target_in = get_time_val(row[in_time_col])
            target_out = get_time_val(row[out_time_col])

            # PDFの中から名前を探す
            name_match = re.search(short_name, full_text)
            
            in_res, out_res = "❌", "❌"
            found_nums = []

            if name_match:
                # 名前の後ろ200文字以内をチェック（出退勤が入る範囲）
                start_idx = name_match.start()
                search_area = full_text[start_idx : start_idx + 200]
                # 3〜4桁の数字を全部拾う
                found_nums = re.findall(r'\d{3,4}', search_area)
                # 頭の0を消して比較用リストを作成
                check_list = [str(int(n)) for n in found_nums]
                
                if target_in in check_list: in_res = "✅"
                if target_out in check_list: out_res = "✅"

            results.append({
                "氏名": raw_name,
                "出勤(CSV)": row[in_time_col], "出勤": in_res,
                "退勤(CSV)": row[out_time_col], "退勤": out_res,
                "付近の数字": found_nums[:5] # 確認用
            })

        st.subheader("📋 照合結果")
        st.table(pd.DataFrame(results))
        with st.expander("AIが読み取った全テキスト"):
            st.text(full_text)
