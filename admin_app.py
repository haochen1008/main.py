import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

# 页面基础设置
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.title("🏡 Hao Harbour 数据管理系统")

def init_connection():
    try:
        # 获取 Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # 强制处理私钥格式：将粘贴时可能出现的 "\\n" 还原为真正的换行
        # 这是修复 InvalidByte(1624, 61) 报错的核心逻辑
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        # 授权并连接
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped_creds)
    except Exception as e:
        st.error(f"❌ 认证配置出错: {e}")
        return None

# 初始化客户端
client = init_connection()

if client:
    try:
        # 使用你截图中的 Sheet ID
        sheet_id = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"
        sh = client.open_by_key(sheet_id)
        
        # 获取第一个工作表
        worksheet = sh.get_worksheet(0)
        
        # UI 按钮：点击刷新
        if st.button("🔄 刷新房源数据"):
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            st.success("✅ 数据同步成功！")
            st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ 无法打开表格: {e}")
        st.info("提示：请确认你的 Google Sheet 已经向 streamlit-bot 账号开启了 Editor 权限。")
