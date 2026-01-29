import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

def get_gc_client():
    try:
        # 读取 Secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # 强制清理私钥：解决 InvalidLength(1625) 的关键
        # 有时候 Secrets 还是会把内容读成带字面量 \n 的字符串
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# 执行读取
client = get_gc_client()
if client:
    try:
        # 表格 ID 依然使用你给的那个
        sh = client.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        df = pd.DataFrame(sh.get_worksheet(0).get_all_records())
        st.success("🎉 数据加载成功！")
        st.dataframe(df)
    except Exception as e:
        st.error(f"密钥解析过了，但读取表格报错: {e}")
