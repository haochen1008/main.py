import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse
import base64

# --- 1. 页面配置与高级暗黑 UI ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 彻底隐藏工具栏 */
    #MainMenu, header, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    
    /* 背景与字体 */
    .stApp {background-color: #0e1117;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="st-"] {font-family: 'Inter', sans-serif; color: #ffffff;}

    /* 提示框美化：毛玻璃效果 */
    .hint-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(191, 160, 100, 0.3);
        color: #bfa064;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
        font-size: 14px;
        line-height: 1.6;
    }

    /* 房源卡片美化 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
        background: #1a1c23;
        border-radius: 15px !important;
        transition: transform 0.3s ease;
        padding: 0px !important;
        overflow: hidden;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }

    /* 按钮美化 */
    .stButton>button {
        background: transparent !important;
        color: #bfa064 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100%;
    }
    .stButton>button:hover {
        background: #bfa064 !important;
        color: #ffffff !important;
    }
    
    /* 精选标签 */
    .featured-tag {
        position: absolute;
        top: 10px;
        left: 10px;
        background: #bfa064;
        color: black;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        z-index: 10;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心函数：统计与弹窗 ---
@st.dialog("Property Details")
def show_details(item):
    # 浏览量统计
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_v.columns:
            df_v.loc[df_v['title'] == item['title'], 'views'] += 1
            conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    st.markdown(f"<h2 style='color:#bfa064; margin-top:0;'>£{item['price']} <span style='font-size:14px; color:#888;'>/pcm</span></h2>", unsafe_allow_html=True)
    
    st.markdown("#### 📖 Highlights")
    st.code(item.get('description', 'No description provided.'), language=None)
    st.caption("✨ Click top-right to copy description")
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("WeChat ID")
    with c2:
        wa_url = f"https://wa.me/447000000000?text=" + urllib.parse.quote(f"Hi, I'm interested in {item['title']}")
        st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
    with c3:
        st.link_button("📞 Call Now", "tel:+447000000000", use_container_width=True)

# --- 3. 顶部品牌展示 ---
def get_base64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_b64 = get_base64("logo.png")
if logo_b64:
    st.markdown(f'<div style="text-align:center; padding:20px;"><img src="data:image/png;base64,{logo_b64}" width="120"></div>', unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align:center; color:#bfa064; letter-spacing:5px; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-weight:300; letter-spacing:4px; font-size:12px; margin-top:0;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

# --- 温馨提示 (优化版样式) ---
st.markdown("""
    <div class="hint-box">
        💡 <b>温馨提示：</b> 由于房源数量众多，网站仅展示部分精选房源。<br>
        如需了解更多伦敦优质房源，请添加微信：<b>HaoHarbour_UK</b> 咨询。
    </div>
""", unsafe_allow_html=True)

# --- 4. 数据加载与筛选 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    with st.expander("🔍 筛选房源 / Filter Options", expanded=False):
        f1, f2, f3 = st.columns(3)
        sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = f2.multiselect("Room Type", options=df['rooms'].unique().tolist())
        max_p = f3.slider("Max Price (£)", 1000, 15000, 15000)

    # 过滤与排序
    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # --- 5. 房源矩阵 (卡片式布局) ---
    st.write("")
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                # 精选标签
                if row.get('is_featured'):
                    st.markdown('<div class="featured-tag">FEATURED</div>', unsafe_allow_html=True)
                
                # 图片
                st.image(row['poster-link'], use_container_width=True)
                
                # 文字详情区 (增加内边距感)
                st.markdown(f"""
                    <div style="padding:15px; text-align:center;">
                        <div style="font-weight:600; font-size:16px; margin-bottom:5px;">{row['title']}</div>
                        <div style="color:#888; font-size:13px; margin-bottom:10px;">📍 {row['region']} | {row['rooms']}</div>
                        <div style="color:#bfa064; font-size:18px; font-weight:bold;">£{row['price']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("View Details", key=f"btn_{idx}"):
                    show_details(row)
except:
    st.info("Searching for the latest properties...")
