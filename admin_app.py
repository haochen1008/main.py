import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import json

# --- 1. 填空区 ---
# 请把你的 JSON 文件内容完整地粘贴在下面两个 r''' 之间
raw_json_str = r'''
{
  "type": "service_account",
  "project_id": "你的项目ID",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n你的私钥内容\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''

# --- 2. 核心连接逻辑 ---
def get_gsheet_client():
    try:
        # 直接解析字符串，不经过 Secrets，格式 100% 保持原样
        info = json.loads(raw_json_str)
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"解析 JSON 失败（请检查粘贴是否完整）: {e}")
        return None

# --- 3. 页面展示 ---
st.set_page_config(page_title="房源管理中心")
st.title("🏡 Hao Harbour 数据管理")

SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🔄 立即刷新表格数据"):
    client = get_gsheet_client()
    if client:
        try:
            with st.spinner("连接中..."):
                # 打开表格并读取
                sheet = client.open_by_key(SHEET_ID).sheet1
                data = sheet.get_all_records()
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
                else:
                    st.warning("表格里好像还没有数据。")
        except Exception as e:
            st.error(f"读取失败: {e}\n请确认你的 Service Account 邮箱是否有权限查看该表格。")
