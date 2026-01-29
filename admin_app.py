import streamlit as st
from google.oauth2 import service_account
import gspread
import pandas as pd

def get_google_client():
    try:
        # 获取 Secrets
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 核心修复：清理私钥。针对 InvalidByte(1624, 61) 报错
        # 1. 将字符串中的字面量 "\n" 替换为真实的换行
        # 2. 去除所有不该存在的空格
        pk = creds_info["private_key"]
        pk = pk.replace("\\n", "\n").replace(" ", "").strip()
        
        # 3. 重新对齐头部和尾部，确保格式严格符合 PEM 标准
        if "-----BEGINPRIVATEKEY-----" in pk:
            pk = pk.replace("-----BEGINPRIVATEKEY-----", "-----BEGIN PRIVATE KEY-----\n")
        if "-----ENDPRIVATEKEY-----" in pk:
            pk = pk.replace("-----ENDPRIVATEKEY-----", "\n-----END PRIVATE KEY-----")
            
        creds_info["private_key"] = pk
        
        # 授权逻辑
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped_creds = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped_creds)
    except Exception as e:
        st.error(f"密钥解析终极报错: {e}")
        return None

# --- UI 展示 ---
st.title("🏡 Hao Harbour 数据管理")
if st.button("🚀 点击同步表格数据"):
    gc = get_google_client()
    if gc:
        try:
            # 使用截图中的表格 ID
            sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
            data = sh.sheet1.get_all_records()
            st.success("🎉 终于成功了！")
            st.dataframe(pd.DataFrame(data))
        except Exception as e:
            st.error(f"验证通过但读取表格报错: {e}")
