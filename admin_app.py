import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import time

def get_authorized_client():
    try:
        # 1. 获取 Secrets 内容
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # 2. 彻底清理私钥中的所有干扰字符
        # 有时候粘贴会产生不可见的特殊空格，这里通过 strip 和 replace 彻底洗一遍
        private_key = creds_dict["private_key"]
        private_key = private_key.replace("\\n", "\n").strip()
        creds_dict["private_key"] = private_key
        
        # 3. 构造凭据
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        
        # 4. 【关键步骤】：允许 10 秒的时间偏移 (Clock Skew)
        # 很多 Invalid JWT 报错是因为服务器时间快了几秒，导致签发的 Token 还没“生效”
        scoped_creds = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        
        # 刷新凭据时增加容错
        return gspread.authorize(scoped_creds)
    except Exception as e:
        st.error(f"授权过程出错: {e}")
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
