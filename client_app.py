import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour", layout="wide")

# --- 2. 深度清理白边与优化 Banner 样式 ---
st.markdown("""
    <style>
    /* 彻底消除 Streamlit 顶部的空白高度 */
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        margin-top: -10px; /* 进一步向上提拉 */
    }
    header {visibility: hidden;} /* 隐藏 Streamlit 原生 Header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 窄横幅容器：背景改为极简白，增加阴影感 */
    .custom-header {
        background-color: #ffffff;
        display: flex;
        align-items: center; /* 垂直居中 */
        justify-content: flex-start; /* 左对齐 */
        padding: 5px 30px;
        height: 1000px; /* 整个横幅只有 70 像素高 */
        border-bottom: 1px solid #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        height: 100%;
    }

    .logo-img {
        max-height: 100px; /* 限制 Logo 高度，宽度会自动缩放 */
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
    </style>
""", unsafe_allow_html=True)

# --- 3. 渲染超窄 Banner ---
logo_path = "logo.jpg"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
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

# --- 4. 数据库连接 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=60)
except Exception:
    st.info("正在更新房源列表...")
    st.stop()

# --- 5. 侧边栏与过滤逻辑 ---
if not df.empty:
    with st.sidebar:
        st.markdown("### 🔍 房源筛选")
        f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
        f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
        
        # 价格转换处理
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        max_p = int(df['price'].max())
        f_price = st.slider("最高预算 (£/pcm)", 0, max_p + 500, max_p + 500)

    filtered = df.copy()
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # --- 6. 房源橱窗展示 ---
    cols = st.columns(3)
    for idx, row in filtered.iterrows():
        with cols[idx % 3]:
            with st.container(border=True):
                st.image(row['poster_link'], use_container_width=True)
                st.markdown(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | {row['rooms']}")
                st.markdown(f"#### :red[£{int(row['price'])} /pcm]")
                
                @st.dialog("联系我们")
                def show_qr(title):
                    st.write(f"正在咨询: **{title}**")
                    if os.path.exists("wechat_qr.png"):
                        st.image("wechat_qr.png", caption="扫码添加微信，获取详细 PDF 资料")
                    else:
                        st.warning("微信二维码 (wechat_qr.png) 尚未上传")

                if st.button("💬 立即咨询", key=f"btn_{idx}", use_container_width=True):
                    show_qr(row['title'])
else:
    st.info("正在努力加载房源...")
