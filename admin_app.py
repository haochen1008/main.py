import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

st.set_page_config(page_title="Hao Harbour 管理", layout="wide")
st.title("🏡 Hao Harbour 数据管理")

def connect_to_gsheets():
    try:
        # 获取 Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 自动处理私钥中的换行符（关键修复步）
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        # 建立授权
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped_credentials = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped_credentials)
    except Exception as e:
        st.error(f"❌ 认证配置失败: {e}")
        return None

# 初始化连接
gc = connect_to_gsheets()

if gc:
    try:
        # 这里的 ID 保持不变
        sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        worksheet = sh.get_worksheet(0)
        
        if st.button("🚀 点击拉取最新房源数据"):
            with st.spinner("正在努力拉取中..."):
                data = worksheet.get_all_records()
                st.success("✅ 数据同步成功！")
                st.dataframe(pd.DataFrame(data), use_container_width=True)
                
    except Exception as e:
        st.error(f"❌ 无法连接到表格: {e}")
        st.info("请确保你的 Google Sheet 已分享给: streamlit-bot@canvas-voltage-278814.iam.gserviceaccount.com 并设为 Editor。")
