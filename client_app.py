import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置与 CSS ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 彻底消除卡片底部空白 */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: -10px !important; }
    
    /* 筛选栏乱码修复 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 12px !important;
    }

    /* WhatsApp 品牌绿按钮 */
    .wa-container {
        background-color: #25D366 !important;
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        display: block;
        margin-top: 10px;
    }

    /* 微信 ID 显眼框 */
    .wechat-box {
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 5px;
    }

    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (顺序完全重构) ---
@st.dialog("Property Details")
def show_details(item):
    # 统计浏览
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    # C. 房源海报 (放在微信和 WhatsApp 后面)
    st.image(item['poster-link'], use_container_width=True)
    
    # D. 标题、价格与地图 (地图在右上角)
    c_title, c_map = st.columns([2, 1])
    with c_title:
        st.markdown(f"### {item['title']}")
        st.markdown(f"<h4 style='color:#bfa064; margin-top:-10px;'>£{item['price']}</h4>", unsafe_allow_html=True)
    with c_map:
        map_q = urllib.parse.quote(item['title'] + " London")
        st.link_button("📍 Open Map", f"https://www.google.com/maps/search/?api=1&query={map_q}", use_container_width=True)

    # E. 描述栏 (保留一键复制)
    st.markdown("---")
    st.markdown("📜 **Description & Available Date**")
    st.code(item.get('description', 'No info'), language=None)

    # A. 微信放在最前面 (最明显)
    st.markdown('<div class="wechat-box"><b>微信咨询 (WeChat):</b></div>', unsafe_allow_html=True)
    st.code("HaoHarbour_UK", language=None)
    
    # B. WhatsApp 紧随其后
    wa_url = f"https://wa.me/447000000000?text=Interested in {item['title']}"
    st.markdown(f'<a href="{wa_url}" class="wa-container">💬 WhatsApp Chat</a>', unsafe_allow_html=True)
    
    st.write("") # 间距
    
    # F. 下载按钮放到最后
    st.write("---")
    try:
        img_data = urllib.request.urlopen(item['poster-link']).read()
        st.download_button("📥 Save Poster", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: pass

# --- 3. 主界面 ---
st.markdown("<h1 style='text-align:center; color:#bfa064;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.warning("💡 更多伦敦优质房源，请咨询微信：HaoHarbour_UK")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    with st.expander("🔍 Filter Options"):
        f1, f2 = st.columns(2)
        sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = f2.multiselect("Rooms", options=df['rooms'].unique().tolist())
        max_p = st.slider("Max Price", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 展示卡片并加入发布日期
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"""
                    <div style='text-align:center; padding:5px;'>
                        <div style='font-weight:bold;'>{row['title']}</div>
                        <div style='color:#bfa064; font-weight:bold;'>£{int(row['price'])}</div>
                        <div style='color:#888; font-size:11px;'>📍 {row['region']} | {row['rooms']}</div>
                        <div style='color:#bbb; font-size:10px;'>📅 {row['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("View Details", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
except:
    st.info("Properties Loading...")
