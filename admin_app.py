import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

def get_authorized_client():
    try:
        # 自动从 Streamlit Secrets 获取 TOML 字典
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 兼容性处理：如果 private_key 还是带了字面量 \n，则强行转义
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        creds = service_account.Credentials.from_service_account_info(creds_info)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"密钥解析阶段出错: {e}")
        return None

# --- UI 展示 ---
st.title("🏡 Hao Harbour 数据管理")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🚀 强制重连并加载数据"):
    client = get_authorized_client()
    if client:
        try:
            # 尝试打开表格，你的 image_607657 显示已授权 Editor 权限
            sh = client.open_by_key(SHEET_ID)
            data = sh.sheet1.get_all_records()
            st.success("🎉 终于连接成功了！")
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(f"验证已过，但读取失败: {e}")
