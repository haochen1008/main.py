import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import base64

# 1. 页面设置
st.set_page_config(page_title="Hao Harbour 管理中心", layout="wide")

# 2. 核心：从 Base64 还原私钥（彻底解决 InvalidPadding 错误）
def get_creds():
    try:
        # 从 Secrets 读取 Base64 字符串
        b64_key = st.secrets["GOOGLE_PRIVATE_KEY_B64"]
        # 解码为原始字符串
        private_key = base64.b64decode(b64_key).decode("utf-8")
        
        info = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": private_key,
            "client_email": st.secrets["GOOGLE_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"密钥解码失败: {e}")
        return None

# 3. 业务逻辑
st.title("🏡 Hao Harbour 房源看板")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("刷新数据"):
    client = get_creds()
    if client:
        try:
            with st.spinner("正在连接 Google Sheets..."):
                sheet = client.open_by_key(SHEET_ID).sheet1
                df = pd.DataFrame(sheet.get_all_records())
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"表格读取失败: {e}")
