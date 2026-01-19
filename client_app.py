import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

# --- 2. 强效 CSS (解决手机重叠与看不清) ---
st.markdown("""
    <style>
    /* 彻底隐藏工具栏 */
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    
    /* 深色背景 */
    .stApp {background-color: #0e1117;}

    /* 修复筛选栏：直接去掉那个导致乱码的箭头 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 8px !important;
    }
    .st-expanderHeader p { color: #bfa064 !important; font-weight: bold; }

    /* 详情页描述框：解决手机端看不清问题 */
    .description-box {
        background-color: #262730 !important;
        color: #ffffff !important;
        padding: 15px;
        border-radius: 10px;
        font-size: 14px;
        line-height: 1.6;
        border-left: 4px solid #bfa064;
        white-space: pre-wrap;
        margin: 10px 0;
    }

    /* 房源卡片 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #1a1c23 !important;
        border: none !important;
        border-radius: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 详情弹窗 ---
@st.dialog("Property Details")
def show_details(item):
    # 统计浏览量
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    st.image(item['poster-link'], use_container_width=True)
    st.markdown(f"### {item['title']}")
    
    # 价格与发布日期
    c_p, c_d = st.columns([1, 1])
    c_p.markdown(f"<h2 style='color:#bfa064; margin:0;'>£{item['price']}</h2>", unsafe_allow_html=True)
    c_d.markdown(f"<p style='text-align:right; color:#888; font-size:12px; margin-top:15px;'>📅 Posted: {item['date']}</p>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("#### 📜 Description & Available Date")
    # 用自定义 HTML 容器替换 st.code，确保手机端绝对清晰
    st.markdown(f'<div class="description-box">{item.get("description", "No info")}</div>', unsafe_allow_html=True)
    
    # 快捷功能按钮
    st.write("---")
    map_q = urllib.parse.quote(f"{item['title']} London")
    st.link_button("🗺️ Open in Google Maps", f"https://www.google.com/maps/search/?api=1&query={map_q}", use_container_width=True)

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("WeChat ID (Copy)")
    with b2:
        wa_url = f"https://wa.me/447000000000?text=Interested in {item['title']}"
        st.link_button("💬 WhatsApp", wa_url, use_container_width=True)

# --- 4. 页面主体 ---
def get_base64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_b64 = get_base64("logo.png")
if logo_b64:
    st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_b64}" width="100"></div>', unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align:center; color:#bfa064;'>HAO HARBOUR</h1>", unsafe_allow_html=True)

st.markdown('<div style="background:rgba(191,160,100,0.1); border:1px solid #bfa064; color:#bfa064; padding:15px; border-radius:10px; text-align:center; font-size:13px; margin-bottom:20px;">💡 网站仅展示部分精选房源，更多信息请咨询微信</div>', unsafe_allow_html=True)

# 数据加载
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 筛选
    with st.expander("🔍 筛选房源 / Filter Options"):
        sel_reg = st.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = st.multiselect("Room", options=df['rooms'].unique().tolist())
        max_p = st.slider("Max Price", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 布局展示
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                # 修复报错位置的 HTML 语法
                title_html = f"<b>{row['title']}</b><br><span style='color:#bfa064;'>£{int(row['price'])}</span>"
                st.markdown(f"<div style='text-align:center; padding:10px;'>{title_html}</div>", unsafe_allow_html=True)
                
                if st.button("View", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
except Exception as e:
    st.error(f"Error loading data: {e}")
