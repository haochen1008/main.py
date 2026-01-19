import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse
import base64

# --- 1. 页面配置与 UI 修复 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 彻底隐藏工具栏 */
    #MainMenu, header, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    
    /* 背景与字体 */
    .stApp {background-color: #0e1117;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="st-"] {font-family: 'Inter', sans-serif; color: #ffffff;}

    /* 修复筛选栏文字重叠 */
    .st-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        line-height: 1.6 !important;
    }
    .st-expanderContent { border: none !important; }

    /* 提示框美化 */
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

    /* 房源卡片 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #1a1c23;
        border-radius: 15px !important;
        transition: transform 0.3s ease;
        padding: 0px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }

    /* 按钮 */
    .stButton>button {
        background: transparent !important;
        color: #bfa064 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* 日期标签样式 */
    .date-tag {
        color: #888;
        font-size: 12px;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (找回丢失的日期) ---
@st.dialog("Property Details")
def show_details(item):
    # 浏览量统计
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    
    # 布局：价格与发布日期
    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.markdown(f"<h2 style='color:#bfa064; margin:0;'>£{item['price']} <span style='font-size:14px; color:#888;'>/pcm</span></h2>", unsafe_allow_html=True)
    with col_info2:
        st.markdown(f"<div style='text-align:right; color:#666; font-size:12px;'>Posted: {item['date']}</div>", unsafe_allow_html=True)

    # 房源亮点
    st.markdown("#### 📖 Highlights")
    st.code(item.get('description', 'No description'), language=None)
    st.caption("✨ Click top-right to copy description")
    
    # 底部联系人与起租日期 (Available Date 通常包含在描述中，也可单独加粗展示)
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

# --- 3. 顶部与提示 ---
def get_base64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_b64 = get_base64("logo.png")
if logo_b64:
    st.markdown(f'<div style="text-align:center; padding:20px;"><img src="data:image/png;base64,{logo_b64}" width="120"></div>', unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align:center; color:#bfa064; letter-spacing:5px;'>HAO HARBOUR</h1>", unsafe_allow_html=True)

st.markdown("""
    <div class="hint-box">
        💡 <b>温馨提示：</b> 由于房源数量众多，网站仅展示部分精选房源。<br>
        如需了解更多伦敦优质房源，请添加微信：<b>HaoHarbour_UK</b> 咨询。
    </div>
""", unsafe_allow_html=True)

# --- 4. 数据展示 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 修复后的筛选栏 (Filter Options)
    with st.expander("🔍 筛选房源 / Filter Options", expanded=False):
        f1, f2, f3 = st.columns(3)
        sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = f2.multiselect("Room Type", options=df['rooms'].unique().tolist())
        max_p = f3.slider("Max Price (£)", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"""
                    <div style="padding:15px; text-align:center;">
                        <div style="font-weight:600; font-size:16px;">{row['title']}</div>
                        <div style="color:#888; font-size:12px;">📍 {row['region']} | {row['rooms']}</div>
                        <div style="color:#bfa064; font-size:18px; font-weight:bold; margin:5px 0;">£{row['price']}</div>
                        <div style="color:#555; font-size:10px;">Posted on: {row['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("View Details", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
except:
    st.info("Loading properties...")
