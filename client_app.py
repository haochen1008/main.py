import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 样式优化：极简 Header + 弹窗修复 ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        margin-top: -45px; 
    }
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 超窄白色横幅样式 */
    .custom-header {
        background-color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 5px 30px;
        height: 70px;
        border-bottom: 1px solid #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        height: 100%;
    }

    .logo-img {
        max-height: 45px;
        width: auto;
        margin-right: 25px;
    }
    
    .header-text {
        border-left: 1px solid #ddd;
        padding-left: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .header-title {
        font-family: 'Times New Roman', serif;
        font-size: 20px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 0;
        line-height: 1.2;
    }
    
    .header-subtitle {
        font-size: 10px;
        color: #888;
        letter-spacing: 3px;
        margin: 0;
        line-height: 1.2;
    }

    .stImage > img {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 定义详情弹窗函数 (必须在按钮点击前定义) ---
@st.dialog("房源详情与联系方式")
def show_details_modal(row_data):
    # 显示海报图
    st.image(row_data['poster-link'], use_container_width=True)
    
    # 显示 DeepSeek 生成的亮点描述
    st.markdown("### 📋 房源亮点")
    st.write(row_data['description'])
    
    st.divider()
    
    # 联系方式
    st.markdown("💬 **联系 Hao Harbour 客服**")
    col_a, col_b = st.columns(2)
    with col_a:
        if os.path.exists("wechat_qr.png"):
            st.image("wechat_qr.png", caption="扫码咨询", width=200)
    with col_b:
        st.write("**微信客服:** HaoHarbour_UK")
        st.write("**咨询房源:** " + row_data['title'])

# --- 4. 渲染极简 Header ---
logo_file = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
if os.path.exists(logo_file):
    with open(logo_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <div class="custom-header">
            <div class="logo-container">
                <img src="data:image/png;base64,{data}" class="logo-img">
            </div>
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">EXCLUSIVE LONDON LIVING</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("### HAO HARBOUR | EXCLUSIVE LONDON LIVING")

# --- 5. 获取数据 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
except Exception:
    st.info("🏠 正在为您更新房源列表...")
    st.stop()

# --- 6. 侧边栏筛选 ---
with st.sidebar:
    st.markdown("### 🔍 房源精选")
    f_reg = st.multiselect("选择区域", options=df['region'].unique().tolist())
    f_rm = st.multiselect("选择房型", options=df['rooms'].unique().tolist())
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    max_val = int(df['price'].max()) if not df.empty else 10000
    f_price = st.slider("最高预算 (£/pcm)", 0, max_val + 500, max_val)

filtered = df.copy()
if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
filtered = filtered[filtered['price'] <= f_price]

# --- 7. 房源展示 ---
st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")

if filtered.empty:
    st.info("暂无匹配房源，请尝试调整筛选条件。")
else:
    cols
