import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

def get_gspread_client():
    try:
        # 1. 从 Secrets 读取原始数据
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 2. 关键修复：去除私钥中由于粘贴产生的多余回车、空格和转义符号
        # 这能解决 image_5fdff3 中的 InvalidLength 错误
        pk = creds_info["private_key"]
        pk = pk.replace("\\n", "\n").replace(" ", "").replace("-----BEGINPRIVATEKEY-----", "-----BEGIN PRIVATE KEY-----\n").replace("-----ENDPRIVATEKEY-----", "\n-----END PRIVATE KEY-----")
        creds_info["private_key"] = pk
        
        # 3. 生成凭据
        creds = service_account.Credentials.from_service_account_info(creds_info)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"密钥解析阶段出错: {e}")
        return None

# 界面部分
st.title("🏡 Hao Harbour 数据管理")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🚀 刷新数据"):
    client = get_gspread_client()
    if client:
        try:
            # 确认权限已在 image_607657 授权
            sh = client.open_by_key(SHEET_ID)
            df = pd.DataFrame(sh.sheet1.get_all_records())
            st.success("🎉 连接成功！")
            st.dataframe(df)
        except Exception as e:
            st.error(f"验证已过，但表格读取失败: {e}")
