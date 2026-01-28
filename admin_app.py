import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

def get_authorized_client():
    try:
        # 获取 Secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # 终极修复：处理所有可能的格式污染
        raw_key = creds_dict["private_key"]
        # 先把字面上的反斜杠n换成回车，再去掉首尾多余的空格/空行
        clean_key = raw_key.replace("\\n", "\n").strip()
        creds_dict["private_key"] = clean_key
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"连接失败（签名仍有问题）: {e}")
        return None

# 界面展示
st.title("🏡 Hao Harbour 房源看板")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🚀 强制重连测试"):
    client = get_authorized_client()
    if client:
        try:
            # 尝试访问
            sh = client.open_by_key(SHEET_ID)
            # 尝试通过索引打开第一个 Sheet
            sheet = sh.get_worksheet(0)
            data = sheet.get_all_records()
            st.success("🎉 验证成功！数据已加载。")
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(f"验证已过，但读取表格内容失败: {e}")
