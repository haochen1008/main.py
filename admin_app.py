import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

# 强制重置连接
def get_data_from_gspread():
    try:
        # 获取 Secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # 核心：处理私钥换行符
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        # 建立连接
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped)
        
        # 打开你的表格
        sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        return pd.DataFrame(sh.sheet1.get_all_records())
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

st.title("🏡 Hao Harbour 数据管理")
if st.button("🚀 刷新数据"):
    df = get_data_from_gspread()
    if df is not None:
        st.dataframe(df)
