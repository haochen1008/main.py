import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread

# 注意：这里不再导入 streamlit_gsheets，彻底避开 ModuleNotFoundError

def get_data():
    try:
        # 1. 直接读取你在 Secrets 里配置的 [gcp_service_account]
        info = dict(st.secrets["gcp_service_account"])
        
        # 2. 自动处理私钥换行符，防止 Invalid JWT Signature
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        # 3. 授权连接
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped)
        
        # 4. 打开表格 (这是你截图中的 ID)
        sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        return pd.DataFrame(sh.sheet1.get_all_records())
    except Exception as e:
        st.error(f"连接失败详情: {e}")
        return None

st.title("🏡 Hao Harbour 数据管理")

if st.button("🚀 重新加载并同步数据"):
    df = get_data()
    if df is not None:
        st.success("🎉 连接成功！")
        st.dataframe(df)
