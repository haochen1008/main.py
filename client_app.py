import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 深度清理白边与极简 Header 样式 ---
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

# --- 3. 定义详情弹窗函数 ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.markdown("### 📋 房源亮点")
    # 显示 DeepSeek 提取的描述
    st.write(item['description'])
    st.divider()
    st.markdown("💬 **联系我们获取详细资料**")
    if os.path.exists("wechat_qr.png"):
        st.image("wechat_qr.png", width=200)
    else:
        st.write("微信客服: HaoHarbour_UK")

# --- 4. 渲染 Header ---
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
    st.info("🏠 正在为您加载最新房源...")
    st.stop()

# --- 6. 侧边栏筛选 ---
with st.sidebar:
    st.markdown("### 🔍 房源精选")
    f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
    f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    max_p = int(df['price'].max()) if not df.empty else 10000
    f_price = st.slider("最高月租 (£/pcm)", 0, max_p + 500, max_p)

filtered = df.copy()
if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
filtered = filtered[filtered['price'] <= f_price]

# --- 7. 房源橱窗展示 ---
st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")

if not filtered.empty:
    # 核心修复：确保 columns 在循环外被正确定义
    main_cols = st.columns(3)
    
    for i, (idx, row) in enumerate(filtered.iterrows()):
        # 依次放入三列中
        col_to_use = main_cols[i % 3]
        
        with col_to_use:
            with st.container(border=True):
                # 封面图
                st.image(row['poster-link'], use_container_width=True)
                
                # 信息描述
                st.markdown(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.markdown(f"#### :red[£{int(row['price']):,} /pcm]")
                
                # 详情按钮：使用 row 的原始索引确保 Key 唯一
                if st.button("查看详情 & 联系", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
else:
    st.warning("没有找到符合条件的房源，请尝试调整筛选。")

# --- 8. 底部 ---
st.divider()
st.caption("© 2026 Hao Harbour Properties.")
