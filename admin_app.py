import streamlit as st
import pandas as pd
import io, requests, cloudinary
import cloudinary.uploader
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. 初始化 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 认证
cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 核心连接函数 ---
def get_gs_conn():
    """
    手动构建连接凭据，避开所有 Secrets 格式解析坑
    """
    try:
        # 1. 手动把 \n 替换成真正的换行符
        # 这样就不需要修改只读的 st.secrets 了
        fixed_key = st.secrets["GS_PRIVATE_KEY"].replace("\\n", "\n")
        
        # 2. 构造标准的 Google 认证字典
        creds = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": fixed_key,
            "client_email": st.secrets["GS_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        # 3. 强制传入字典，不传任何额外参数防止冲突
        return st.connection("gsheets", type=GSheetsConnection, **creds)
    except Exception as e:
        st.error(f"连接初始化失败: {e}")
        return None

# --- 3. UI 逻辑 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

with tab1:
    st.subheader("🚀 发布新房源")
    n_title = st.text_input("房源名称")
    n_raw = st.text_area("英文描述")
    n_pics = st.file_uploader("上传图片", accept_multiple_files=True)
    
    if st.button("📤 确认发布", type="primary"):
        try:
            with st.spinner("处理中..."):
                # 图片上传
                img_url = ""
                if n_pics:
                    img_url = cloudinary.uploader.upload(n_pics[0])['secure_url']
                
                # 数据同步
                conn = get_gs_conn()
                df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0)
                new_data = pd.DataFrame([{
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": n_title,
                    "poster-link": img_url,
                    "description": n_raw
                }])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=updated_df)
                st.success("发布成功！")
        except Exception as e:
            st.error(f"发布错误: {e}")

with tab2:
    st.subheader("📊 房源看板")
    if st.button("🔄 刷新数据"):
        try:
            conn = get_gs_conn()
            df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")
