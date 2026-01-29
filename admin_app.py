import streamlit as st
from google.oauth2 import service_account
import gspread
import pandas as pd

def get_authorized_client():
    try:
        # 1. 直接拿 Secrets
        info = dict(st.secrets["gcp_service_account"])
        
        # 2. 强行清理私钥头部（防止粘贴时多了个空格或少个换行）
        pk = info["private_key"]
        if not pk.startswith("-----BEGIN"):
            pk = "-----BEGIN PRIVATE KEY-----\n" + pk
        if not pk.endswith("-----END PRIVATE KEY-----"):
            pk = pk + "\n-----END PRIVATE KEY-----"
            
        info["private_key"] = pk
        
        # 3. 验证并授权
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# 测试连接
st.title("🏡 Hao Harbour 数据管理")
if st.button("🚀 立即加载数据"):
    client = get_authorized_client()
    if client:
        try:
            # 确认你已经在表格里给 streamlit-bot@ 授权了 Editor 权限
            sh = client.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
            data = sh.get_worksheet(0).get_all_records()
            st.success("🎉 数据读取成功！")
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(f"密钥对了，但表格读取失败: {e}")
