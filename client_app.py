import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 强力排版修正 (针对移动端) ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 彻底清理重叠文字 */
    .st-expanderHeader > div:first-child { display: none !important; } /* 移除那个出错的箭头图标 */
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        padding: 10px !important;
        border-radius: 8px !important;
        color: #bfa064 !important;
        font-size: 14px !important;
    }

    /* 详情页描述框深度美化 (解决手机看不清的问题) */
    code {
        color: #ffffff !important; /* 强制白色文字 */
        background-color: #262730 !important; /* 深色背景 */
        padding: 15px !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        border-radius: 10px !important;
        display: block !important;
        white-space: pre-wrap !important;
        border-left: 3px solid #bfa064 !important;
    }

    /* 隐藏不必要的侧边栏和多余组件 */
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    
    /* 房源卡片手机端适配 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #1a1c23 !important;
        border-radius: 12px !important;
        margin-bottom: 20px !important;
    }

    /* 提示框 */
    .hint-box {
        background: rgba(191, 160, 100, 0.1);
        border: 1px solid #bfa064;
        color: #bfa064;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
        font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (恢复地图与高对比度) ---
@st.dialog("Property Details")
def show_details(item):
    # 统计点击量
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    st.image(item['poster-link'], use_container_width=True)
    st.markdown(f"<h3 style='margin-bottom:0;'>{item['title']}</h3>", unsafe_allow_html=True)
    
    col_p, col_d = st.columns([1, 1])
    col_p.markdown(f"<h2 style='color:#bfa064; margin:0;'>£{item['price']}</h2>", unsafe_allow_html=True)
    col_d.markdown(f"<p style='text-align:right; color:#888; font-size:12px; padding-top:15px;'>📅 Posted: {item['date']}</p>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("#### 📜 Description & Available Date")
    # 使用 st.code 解决一键复制和手机端清晰度问题
    st.code(item.get('description', '暂无描述'), language=None)
    
    st.write("---")
    # 这里可以嵌入地图链接
    st.markdown("#### 📍 Location")
    map_query = urllib.parse.quote(f"{item['title']} London")
    st.link_button("🗺️ Open in Google Maps", f"https://www.google.com/maps/search/?api=1&query={map_query}", use_container_width=True)

    st.divider()
    c1, c2 = st.columns(2)
    c1.code("HaoHarbour_UK", language=None)
    wa_url = f"https://wa.me/447000000000?text=Hi, info for {item['title']}"
    c2.link_button("💬 WhatsApp", wa_url, use_container_width=True)

# --- 3. 页面内容 ---
def get_base64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

logo_b64 = get_base64("logo.png")
if logo_b64:
    st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_b64}" width="100"></div>', unsafe_allow_html=True)

st.markdown("""<div class="hint-box">💡 网站仅展示部分精选房源，更多信息请咨询微信</div>""", unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 筛选栏
    with st.expander("🔍 筛选房源 / Filter Options", expanded=False):
        sel_reg = st.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = st.multiselect("Room", options=df['rooms'].unique().tolist())
        max_p = st.slider("Max Price", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 手机端一列，大屏三列
    cols = st.columns(1 if st.session_state.get('is_mobile', False) else 3)
    # 自动适配：Streamlit 默认会自动根据宽度调整，我们直接循环
    for i, (idx, row) in enumerate(f_df.iterrows()):
        container_col = i % 3 if not st.session_state.get('is_mobile', False) else 0
        with st.columns(3)[container_col] if not st.session_state.get('is_mobile', False) else st.container():
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"<div style='text-align:center; padding:10px;'><b>{row['title']}</b><br><span style='color:#bfa064;'>£{row['price']}</span></div>", unsafe_allow_html=True
