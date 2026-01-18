import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour", layout="wide")

# --- 2. 核心 CSS 样式（控制超窄横幅和去白边） ---
st.markdown("""
    <style>
    /* 1. 消除顶部巨大的空白 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. 定义超窄横幅样式 */
    .custom-header {
        background-color: #ffffff;
        border-bottom: 1px solid #eeeeee;
        display: flex;
        align-items: center;
        padding: 10px 20px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    
    .logo-img {
        height: 50px; /* 强制 Logo 高度为 50 像素，非常窄 */
        margin-right: 20px;
    }
    
    .header-text {
        border-left: 1px solid #ccc;
        padding-left: 20px;
    }
    
    .header-title {
        font-family: 'serif';
        font-size: 22px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 0;
    }
    
    .header-subtitle {
        font-size: 12px;
        color: #666;
        letter-spacing: 2px;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 渲染超窄横幅 ---
# 我们改用直接读 Logo 文件配合 CSS 的方式
logo_path = "logo.jpg" # 请确保 GitHub 上的文件名叫 logo.png
if os.path.exists(logo_path):
    import base64
    def get_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    logo_base64 = get_base64(logo_path)
    
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{logo_base64}" class="logo-img">
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">EXCLUSIVE LONDON LIVING</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("### HAO HARBOUR | EXCLUSIVE LONDON LIVING")

# --- 4. 数据库连接 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=60)
except Exception:
    st.error("正在同步房源数据...")
    st.stop()

# --- 5. 侧边栏与过滤逻辑 ---
if not df.empty:
    with st.sidebar:
        st.markdown("### 🔍 房源筛选")
        f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
        f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
        
        prices = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        max_p = int(prices.max())
        f_price = st.slider("最高预算 (£/pcm)", 0, max_p + 500, max_p + 500)

    filtered = df.copy()
    filtered['price'] = pd.to_numeric(filtered['price'], errors='coerce')
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # --- 6. 展示房源 ---
    cols = st.columns(3)
    for idx, row in filtered.iterrows():
        with cols[idx % 3]:
            with st.container(border=True):
                st.image(row['poster_link'], use_container_width=True)
                st.markdown(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | {row['rooms']}")
                st.markdown(f"#### :red[£{row['price']}]")
                
                @st.dialog("联系我们")
                def show_qr(title):
                    st.write(f"咨询房源: {title}")
                    if os.path.exists("wechat_qr.png"):
                        st.image("wechat_qr.png")
                    st.info("扫码添加微信，获取详细 PDF 资料")

                if st.button("💬 立即咨询", key=f"b_{idx}", use_container_width=True):
                    show_qr(row['title'])
else:
    st.info("正在加载精选房源...")
