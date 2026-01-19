import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64
import io

# --- 1. 页面配置与顶级 CSS ---
st.set_page_config(page_title="Hao Harbour | London Excellence", layout="wide")

st.markdown("""
    <style>
    /* 彻底解决手机端筛选栏重叠 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    .st-expanderHeader p { color: #bfa064 !important; font-size: 16px !important; font-weight: 600 !important; }

    /* 恢复高级感房源卡片 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #1a1c23 !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0px !important;
        overflow: hidden;
    }
    
    /* 描述框：白底黑字，确保手机绝对清晰 */
    .desc-container {
        background-color: #f8f9fa !important;
        color: #1a1c23 !important;
        padding: 20px;
        border-radius: 12px;
        font-size: 15px;
        line-height: 1.8;
        border-left: 5px solid #bfa064;
        margin: 15px 0;
        white-space: pre-wrap;
    }

    /* 隐藏杂项 */
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心功能：详情弹窗 ---
@st.dialog("Property Details")
def show_details(item):
    # 浏览量统计
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    # 图片与标题
    st.image(item['poster-link'], use_container_width=True)
    st.markdown(f"## {item['title']}")
    
    col1, col2 = st.columns([1, 1])
    col1.markdown(f"<h3 style='color:#bfa064; margin:0;'>£{item['price']} <small>/pcm</small></h3>", unsafe_allow_html=True)
    col2.markdown(f"<p style='text-align:right; color:#888; font-size:12px; padding-top:15px;'>📅 Posted: {item['date']}</p>", unsafe_allow_html=True)

    # 1. 一键复制功能 (使用 st.code 触发)
    st.write("---")
    st.markdown("#### 📜 Description & Available Date")
    # 这里用 st.code 是为了让用户点击右上角就能一键复制所有文字
    st.code(item.get('description', '暂无描述'), language=None)
    
    # 2. 海报下载功能
    st.write("---")
    try:
        img_res = urllib.request.urlopen(item['poster-link']).read()
        st.download_button(label="📥 下载房源海报 (Save Poster)", data=img_res, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: st.warning("海报下载暂时不可用")

    # 3. 地图跳转
    map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(item['title'] + ' London')}"
    st.link_button("📍 在 Google Maps 中查看位置", map_url, use_container_width=True)

    st.divider()
    b1, b2 = st.columns(2)
    b1.code("HaoHarbour_UK", language=None) # 微信号复制
    wa_url = f"https://wa.me/447000000000?text=Hi, info for {item['title']}"
    b2.link_button("💬 WhatsApp", wa_url, use_container_width=True)

# --- 3. 主界面 ---
st.markdown("<h1 style='text-align:center; color:#bfa064; letter-spacing:5px;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:12px; letter-spacing:3px; margin-top:-15px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

st.markdown('<div style="background:rgba(191,160,100,0.1); border:1px solid #bfa064; color:#bfa064; padding:15px; border-radius:10px; text-align:center; font-size:13px; margin: 20px 0;">💡 网站仅展示部分精选房源，更多信息请咨询微信</div>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 筛选栏优化
    with st.expander("🔍 筛选房源 / Filter Options", expanded=False):
        c1, c2, c3 = st.columns(3)
        sel_reg = c1.multiselect("区域 (Region)", options=df['region'].unique().tolist())
        sel_room = c2.multiselect("房型 (Rooms)", options=df['rooms'].unique().tolist())
        max_p = c3.slider("预算 (£ Max)", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 房源展示
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"""
                    <div style='text-align:center; padding:15px;'>
                        <div style='font-size:16px; font-weight:bold; margin-bottom:5px;'>{row['title']}</div>
                        <div style='color:#bfa064; font-size:18px; font-weight:800;'>£{int(row['price'])}</div>
                        <div style='color:#888; font-size:12px;'>📍 {row['region']} | {row['rooms']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("查看详情 (View)", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
except Exception as e:
    st.info("Property data loading...")
