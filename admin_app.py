import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

st.title("🏡 Hao Harbour 数据管理")

def load_data():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped)
        
        # --- 修改这里：改用 URL 打开 ---
        sheet_url = "https://docs.google.com/spreadsheets/d/1wZjOJpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74/edit#gid=0"
        sh = gc.open_by_url(sheet_url)
        # ----------------------------
        
        worksheet = sh.get_worksheet(0)
        return pd.DataFrame(worksheet.get_all_records())
        
    except Exception as e:
        st.error(f"❌ 还是不行: {e}")
        return None

if st.button("🚀 尝试通过 URL 强制连接"):
    df = load_data()
    if df is not None:
        st.success("🎉 终于成功了！")
        st.dataframe(df)
