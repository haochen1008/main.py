import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置与 CSS 深度优化 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 解决卡片内部太挤的问题 */
    .property-info-container {
        padding: 20px 10px !important; /* 增加上下内边距 */
        text-align: center;
    }
    .prop-title { font-weight: bold; font-size: 18px; margin-bottom: 8px; }
    .prop-price { color: #bfa064; font-size: 20px; font-weight: bold; margin-bottom: 12px; }
    .prop-tags { color: #888; font-size: 13px; margin-bottom: 8px; }
    .prop-date { color: #bbb; font-size: 12px; margin-top: 10px; border-top: 1px solid #eee; padding-top: 8px; }

    /* 修复筛选栏 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 12px !important;
    }

    /* WhatsApp 绿色按钮 */
    .wa-link {
        background-color: #25D366 !important;
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        display: block;
        margin: 10px 0;
    }

    /* 微信 ID 容器 */
    .wechat-header {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        border: 1px solid #eee;
        border-bottom: none;
    }

    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (顺序：微信->WhatsApp->海报->信息->描述) ---
@st.dialog("Property Details")
def show_details(item):
    # 统计
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

    # 3. 房源海报
    st.image(item['poster-link'], use_container_width=True)
    
    # 4. 标题与地图
    c_t, c_m = st.columns([2, 1])
    with c_t:
        st.markdown(f"### {item['title']}")
        st.markdown(f"<h4 style='color:#bfa064; margin-top:-10px;'>£{item['price']}</h4>", unsafe_allow_html=True)
    with c_m:
        m_q = urllib.parse.quote(item['title'] + " London")
        st.link_button("📍 Open Map", f"https://www.google.com/maps/search/?api=1&query={m_q}", use_container_width=True)

    # 5. 描述
    st.markdown("---")
    st.markdown("📜 **Description (Click to Copy)**")
    st.code(item.get('description', 'No info'), language=None)

        # 1. 微信 (置顶)
    st.markdown('<div class="wechat-header"><b>微信咨询 (WeChat):</b></div>', unsafe_allow_html=True)
    st.code("HaoHarbour_UK", language=None)
    
    # 2. WhatsApp
    wa_url = f"https://wa.me/447000000000?text=Interested in {item['title']}"
    st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp Chat</a>', unsafe_allow_html=True)
    
    # 6. 下载
    st.write("---")
    try:
        img_data = urllib.request.urlopen(item['poster-link']).read()
        st.download_button("📥 Save Poster to Phone", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: pass

# --- 3. 主界面 ---
st.markdown("<h1 style='text-align:center; color:#bfa064; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:12px; margin-top:0; letter-spacing:3px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

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

    # 展示房源卡片
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        # 找到 for 循环这一行，替换其内部逻辑：
    cols = st.columns(3)
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            # --- 核心修改：增加一个相对定位的容器来放标签 ---
            st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
            
            # 判断是否为精选房源，是则显示标签
            if row.get('is_featured') == 1 or str(row.get('is_featured')).lower() == 'true':
                st.markdown("""
                    <div style="
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background-color: #ff4b4b;
                        color: white;
                        padding: 4px 12px;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        z-index: 10;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    ">🌟 精选房源</div>
                """, unsafe_allow_html=True)

            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"""
                    <div class="property-info-container">
                        <div class="prop-title">{row['title']}</div>
                        <div class="prop-price">£{int(row['price'])}</div>
                        <div class="prop-tags">📍 {row['region']} | {row['rooms']}</div>
                        <div class="prop-date">发布日期: {row['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("View Details", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
            
            st.markdown('</div>', unsafe_allow_html=True) # 闭合相对定位容器
except:
    st.info("Loading properties...")
