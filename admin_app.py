import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

def get_authorized_client():
    try:
        # 直接从 Streamlit Secrets 读取刚才存进去的配置
        # 这会自动处理所有的格式问题
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # 强制处理换行符，确保签名 100% 正确
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"密钥加载失败: {e}")
        return None

st.title("🏡 Hao Harbour 房源管理")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🔄 刷新房源看板"):
    client = get_authorized_client()
    if client:
        try:
            # 打开表格
            sh = client.open_by_key(SHEET_ID)
            sheet = sh.sheet1
            data = sheet.get_all_records()
            st.success("🎉 数据加载成功！")
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        except Exception as e:
            st.error(f"读取数据失败: {e}")
