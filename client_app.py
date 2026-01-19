import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
import requests

# --- 1. 页面配置与字体导入 ---
st.set_page_config(page_title="Hao Harbour | London Excellence", layout="wide")

# 引入 Google Fonts 高端字体
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Playfair+Display:wght@700&display=swap');
    
    /* 基础背景与字体设置 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* 标题样式 */
    h1, h2, h3, .header-title {
        font-family: 'Playfair Display', serif !important;
    }

    /* 隐藏 Streamlit 默认组件 */
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 0rem !important; margin-top: -40px; }

    /* 高端 Header 样式 */
    .custom-header {
        background-color: white;
        display: flex;
        align-items: center;
        padding: 10px 40px;
        border-bottom: 0.5px solid #EAEAEA;
        margin-bottom: 30px;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .logo-img { max-height: 45px; margin-right: 20px; }
    .header-text { border-left: 1px solid #333; padding-left: 20px; }
    .header-title { font-size: 22px; letter-spacing: 1px; color: #1A1A1A; margin: 0; }
    .header-subtitle { font-size: 10px; color: #999; letter-spacing: 3px; text-transform: uppercase; margin-top: 2px; }

    /* 房源卡片升级 */
    [data-testid="stVerticalBlock"] > div:has(div.stExpander) { border:none; }
    .stImage > img { border-radius: 4px; transition: transform 0.3s ease; }
    .stImage > img:hover { transform: scale(1.02); }
    
    /* 标签样式 */
    .status-tag {
        background-color: #000000;
        color: white;
        padding: 2px 8px;
        font-size: 10px;
        text-transform: uppercase;
        border-radius: 2px;
        margin-bottom: 8px;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (保持极简联系逻辑) ---
@st.dialog("Property Details")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.markdown(f"<div class='status-tag'>Newly Added</div>", unsafe_allow_html=True)
    st.markdown(f"### {item['title']}")
    st.caption(f"📅 Available from: {item['date']}")
    
    st.markdown("---")
    st.markdown("#### Highlights")
    st.write(item['description'])
    st.markdown("---")
    
    # 联系方式
    wechat_id = "HaoHarbour_UK"
    phone_num = "447000000000"
    
    st.markdown("💬 **Consultation**")
    st.code(wechat_id, language=None)
    st.caption("Click ID to copy and search on WeChat")
    
    c1, c2 = st.columns(2)
    with c1:
        wa_url = f"https://wa.me/{phone_num}?text=Inquiry: {item['title']}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; height:45px; background:#000; color:#FFF; border:none; font-weight:600; cursor:pointer;">WhatsApp</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="tel:+{phone_num}"><button style="width:100%; height:45px; background:#FFF; color:#000; border:1px solid #000; font-weight:600; cursor:pointer;">Call Now</button></a>', unsafe_allow_html=True)

# --- 3. 渲染高端 Header ---
logo_file = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
if os.path.exists(logo_file):
    with open(logo_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{data}" class="logo-img">
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">Luxury Real Estate London</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. 数据加载与处理 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
    # 置顶逻辑
    df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values(by='date_dt', ascending=False)
except:
    st.stop()

# --- 5. 极简筛选器 ---
with st.container():
    c1, c2, c3 = st.columns([1,1,1])
    with c1: f_reg = st.selectbox("Region", ["All Regions"] + df['region'].unique().tolist())
    with c2: f_rm = st.selectbox("Rooms", ["All Types"] + df['rooms'].unique().tolist())
    with c3: 
        max_p = int(df['price'].max())
        f_price = st.slider("Max Budget (£)", 0, max_p + 500, max_p)

# 过滤逻辑
filtered = df.copy()
if f_reg != "All Regions": filtered = filtered[filtered['region'] == f_reg]
if f_rm != "All Types": filtered = filtered[filtered['rooms'] == f_rm]
filtered = filtered[filtered['price'] <= f_price]

# --- 6. 房源展示网格 ---
st.markdown(f"<p style='color:#666; font-size:12px;'>Found {len(filtered)} Premier Properties</p>", unsafe_allow_html=True)

main_cols = st.columns(3)
for i, (idx, row) in enumerate(filtered.iterrows()):
    with main_cols[i % 3]:
        # 外层容器实现极简卡片感
        st.image(row['poster-link'], use_container_width=True)
        st.markdown(f"<div style='margin-top:10px;'><span class='status-tag'>Featured</span></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-family:\"Playfair Display\"; font-size:18px; font-weight:bold; margin-bottom:0;'>{row['title']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#666; font-size:13px;'>{row['region']} · {row['rooms']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:20px; font-weight:600; color:#000;'>£{int(row['price']):,} <small style='font-size:12px; font-weight:normal;'>/pcm</small></p>", unsafe_allow_html=True)
        
        if st.button("View Details", key=f"view_{idx}", use_container_width=True):
            show_details(row)
        st.write("") # 间距
