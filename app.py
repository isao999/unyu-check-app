import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import pytesseract
import re

st.title("運送業務・照合ツール（出退勤セット版）")

pdf_file = st.file_uploader("点呼記録簿（PDF）をアップロード", type="pdf")
csv_file = st.file_uploader("出退勤CSVをアップロード", type="csv")

if pdf_file and csv_file:
    # --- 1. CSVの読み込み ---
    try:
        df_csv = pd.read_csv(csv_file, encoding='cp932')
        st.success("CSVを読み込んだよ！")
    except Exception as e:
        st.error(f"CSVエラー: {e}")
        st.stop()

    # --- サイドバーで列を選択 ---
    st.sidebar.header("CSVの列設定")
    cols = df_csv.columns.tolist()
    
    name_col = st.sidebar.selectbox("氏名の列", cols)
    in_time_col = st.sidebar.selectbox("「出勤」時間の列", cols)
    out_time_col = st.sidebar.selectbox("「退勤」時間の列", cols)

    if st.button("出退勤をまとめて照合！"):
        st.info("解析中... 手書き文字の中から出勤と退勤の両方を探しています。")

        # --- 2. PDFの解析 ---
        try:
            images = convert_from_bytes(pdf_file.read(), dpi=300)
            full_text = ""
            for img in images:
                # 現場の文字を根こそぎ拾う設定
                full_text += pytesseract.image_to_string(img, lang="jpn+eng", config='--psm 11')
            
            # 検索しやすいように空白を削除
            full_text = re.sub(r'\s+', '', full_text)
        except Exception as e:
            st.error(f"PDF解析エラー: {e}")
            st.stop()

        # --- 3. 照合ロジック ---
        results = []
        
        for _, row in df_csv.iterrows():
            name = str(row[name_col]).replace(" ", "").replace("　", "")
            
            # CSVの時間を数字だけにする関数
            def clean_time(t):
                s = str(t).replace(":", "").replace(".", "")
                return str(int(s)) if s.isdigit() else s

            csv_in = clean_time(row[in_time_col])
            csv_out = clean_time(row[out_time_col])

            # PDFから名前を探す
            name_idx = full_text.find(name)
            
            in_status = "❌ 不明"
            out_status = "❌ 不明"
            detail = "名前が見つかりません"

            if name_idx != -1:
                # 名前の後ろ100文字以内を探索範囲にする（出退勤両方入るように少し広めたよ）
                search_area = full_text[name_idx : name_idx + 100]
                pdf_numbers = [str(int(n)) for n in re.findall(r'\d{3,4}', search_area)]
                
                # 出勤の照合
                if csv_in in pdf_numbers:
                    in_status = "✅ 一致"
                
                # 退勤の照合
                if csv_out in pdf_numbers:
                    out_status = "✅ 一致"
                
                detail = f"付近の数字: {pdf_numbers}"
            
            results.append({
                "氏名": name,
                "出勤(CSV)": row[in_time_col],
                "出勤判定": in_status,
                "退勤(CSV)": row[out_time_col],
                "退勤判定": out_status,
                "備考": detail
            })

        # 結果をテーブルで表示
        st.subheader("📋 照合結果")
        st.table(pd.DataFrame(results))

        with st.expander("AIが読み取った全テキスト（確認用）"):
            st.text(full_text)
