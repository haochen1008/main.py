import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

def safe_connect():
    try:
        # 获取 Secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # 核心：将粘贴进去的字面量 \n 替换为真实的系统换行符
        # 这一步是修复 InvalidByte(1624, 61) 的唯一方法
        clean_key = info["private_key"].replace("\\n", "\n")
        info["private_key"] = clean_key
        
        # 授权
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

st.title("🏡 Hao Harbour 数据管理")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🚀 深度连接"):
    gc = safe_connect()
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            df = pd.DataFrame(sh.sheet1.get_all_records())
            st.success("终于连接成功了！")
            st.dataframe(df)
        except Exception as e:
            st.error(f"密钥对了，但读取表格失败: {e}")
