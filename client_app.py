import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置与增强版 CSS ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 彻底解决筛选栏乱码与重叠 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    .st-expanderHeader p { color: #bfa064 !important; font-weight: 600 !important; }

    /* 房源卡片紧凑化：解决下方空白过多问题 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border-radius: 15px !important;
        padding: 0px !important;
        margin-bottom: -15px !important; /* 减少卡片间距 */
    }
    
    /* 按钮美化 */
    .stButton>button {
        background-color: #f8f9fa !important;
        color: #1a1c23 !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        height: 45px !important;
    }

    /* WhatsApp 专用绿色 */
    .wa-btn {
        background-color: #25D366 !important;
        color: white !important;
        text-decoration: none;
        padding: 10px;
        border-radius: 8px;
        display: block;
        text-align: center;
        font-weight: bold;
    }

    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (重构布局) ---
@st.dialog("Property Details")
def show_details(item):
    # 统计点击
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    # 1. 顶部：微信与 WhatsApp (置顶显眼)
    c1, c2 = st.columns(2)
    with c1:
        st.error(f"微信加我: {st.code('HaoHarbour_UK')}") # 用红色提示框包裹更显眼
    with c2:
        wa_url = f"https://wa.me/447000000000?text=Interested in {item['title']}"
        st.markdown(f'<a href="{wa_url}" class="wa-btn">🟢 WhatsApp Chat</a>', unsafe_allow_html=True)

    st.image(item['poster-link'], use_container_width=True)
    
    # 2. 描述栏 (地图移至右上角)
    head_col, map_col = st.columns([3, 2])
    with head_col:
        st.markdown(f"## {item['title']}")
        st.markdown(f"<h3 style='color:#bfa064; margin-top:-15px;'>£{item['price']} <small>/pcm</small></h3>", unsafe_allow_html=True)
    with map_col:
        # 地图放到这里
        map_q = urllib.parse.quote(item['title'] + " London")
        st.link_button("📍 Open Map", f"https://www.google.com/maps/search/?api=1&query={map_q}", use_container_width=True)

    st.write("---")
    st.markdown("#### 📜 Description (Click to Copy)")
    st.code(item.get('description', 'No info'), language=None) # 保留一键复制
    
    # 3. 底部：下载海报
    st.write("---")
    try:
        img_data = urllib.request.urlopen(item['poster-link']).read()
        st.download_button("📥 Save Poster to Phone", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: pass

# --- 3. 主界面布局 ---
st.markdown("<h1 style='text-align:center; color:#bfa064; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:12px; margin-top:0;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

# 提示语优化
st.warning("💡 由于房源数量众多，仅展示部分精选房源。了解更多请咨询微信：HaoHarbour_UK")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    with st.expander("🔍 筛选房源 / Filter Properties", expanded=False):
        f1, f2 = st.columns(2)
        sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = f2.multiselect("Rooms", options=df['rooms'].unique().tolist())
        max_p = st.slider("Max Price (£)", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 4. 房源卡片：加入发布日期显示
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                # 调整下方文字间距，解决空白过多问题
                st.markdown(f"""
                    <div style='text-align:center; padding:10px;'>
                        <div style='font-weight:bold; font-size:15px;'>{row['title']}</div>
                        <div style='color:#bfa064; font-size:16px; font-weight:bold;'>£{int(row['price'])}</div>
                        <div style='color:#888; font-size:11px;'>📍 {row['region']} | {row['rooms']}</div>
                        <div style='color:#bbb; font-size:10px; margin-top:5px;'>📅 Posted: {row['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("查看详情 (View)", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
except:
    st.info("Loading properties...")
