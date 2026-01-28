import streamlit as st
import pandas as pd
import requests, cloudinary
import cloudinary.uploader
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 初始化 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 核心连接函数 (确保缩进正确) ---
def get_gs_conn():
    try:
        # 手动修正换行符问题
        pk = st.secrets["GS_KEY"].replace("\\n", "\n")
        # 构造纯字典认证
        creds = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": pk,
            "client_email": st.secrets["GS_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        # 直接建立连接
        return st.connection("gsheets", **creds)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# --- UI 界面 ---
tab1, tab2 = st.tabs(["🚀 发布房源", "📊 管理中心"])

with tab1:
    st.subheader("录入房源")
    n_title = st.text_input("名称")
    n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
    n_price = st.number_input("月租 (£)", value=3000)
    n_desc = st.text_area("文案内容")
    n_pics = st.file_uploader("图片", type=['jpg', 'png'])

    if st.button("📤 立即发布", type="primary"):
        if n_title and n_pics:
            try:
                with st.spinner("同步中..."):
                    url = cloudinary.uploader.upload(n_pics)['secure_url']
                    conn = get_gs_conn()
                    # 明确 URL，避开自动读取 bug
                    df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
                    new_data = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "title": n_title,
                        "region": n_reg,
                        "price": n_price,
                        "poster-link": url,
                        "description": n_desc
                    }])
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=updated_df)
                    st.success("发布成功！")
            except Exception as e:
                st.error(f"操作失败: {e}")

with tab2:
    st.subheader("现有房源")
    if st.button("🔄 刷新看板"):
        try:
            conn = get_gs_conn()
            df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")
