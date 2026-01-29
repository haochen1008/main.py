import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

# 设置页面
st.set_page_config(page_title="Hao Harbour 管理", layout="wide")
st.title("🏡 Hao Harbour 数据管理")

def load_data():
    try:
        # 直接获取 Secrets 字典
        # 此时不再手动处理 private_key，让库自己去读刚才在 Secrets 里贴好的原始格式
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 建立授权
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped_credentials = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped_credentials)
        
        # 打开你的表格
        sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        worksheet = sh.get_worksheet(0)
        
        # 读取数据
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
        
    except Exception as e:
        # 如果报错，我们打印出报错的类型，方便精准定位
        st.error(f"❌ 连接失败原因: {type(e).__name__} - {e}")
        return None

# UI 交互
if st.button("🚀 立即拉取房源数据"):
    with st.spinner("正在连接 Google Sheets..."):
        df = load_data()
        if df is not None:
            st.success("✅ 数据拉取成功！")
            st.dataframe(df, use_container_width=True)
