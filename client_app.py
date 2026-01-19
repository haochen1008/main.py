import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse

# --- 1. 彻底隐藏右上角 GitHub 与 Streamlit 菜单 ---
st.set_page_config(page_title="Hao Harbour | London Excellence", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stToolbar"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗逻辑 (保留所有交互功能) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    st.write(f"💰 **Monthly Rent: £{item['price']}**")
    st.markdown(item.get('description', '暂无详细说明'))
    st.divider()

    # 咨询与工具
    c1, c2, c3 = st.columns(3)
    with c1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("微信 ID (点击复制)")
    with c2:
        phone = "447000000000" # 请修改为你的号码
        wa_url = f"https://wa.me/{phone}?text=" + urllib.parse.quote(f"Hi, I am interested in {item['title']}")
        st.link_button("💬 WhatsApp咨询", wa_url, use_container_width=True)
    with c3:
        st.link_button("📞 拨打电话", f"tel:+{phone}", use_container_width=True)

    c4, c5 = st.columns(2)
    with c4:
        map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(item['title'] + ', London')}"
        st.link_button("📍 Google Maps", map_url, use_container_width=True)
    with c5:
        try:
            img_data = requests.get(item['poster-link']).content
            st.download_button("📥 下载海报", data=img_data, file_name=f"{item['title']}.jpg", use_container_width=True)
        except: pass

    # 后台浏览量统计 (静默)
    try:
        conn_u = st.connection("gsheets", type=GSheetsConnection)
        df_u = conn_u.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_u.columns:
            df_u.loc[df_u['title'] == item['title'], 'views'] += 1
            conn_u.update(worksheet="Sheet1", data=df_u)
    except: pass

# --- 3. 顶部 Logo 与 Banner ---
# 请将这里的 URL 替换为你 Cloudinary 里的 Logo 地址
LOGO_URL = "https://res.cloudinary.com/your_cloud_name/image/upload/v12345/your_logo.png"

st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <img src="{LOGO_URL}" width="150">
        <h1 style="margin-top: 10px; color: #1a1a1a;">HAO HARBOUR</h1>
        <p style="color: #bfa064; font-weight: bold; letter-spacing: 2px;">EXCLUSIVE LONDON LIVING</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. 找回筛选器功能 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')

    with st.expander("🔍 筛选房源 (Filter Properties)", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            sel_region = st.multiselect("区域 (Region)", options=df['region'].unique(), default=df['region'].unique())
        with f2:
            sel_rooms = st.multiselect("房型 (Room Type)", options=df['rooms'].unique(), default=df['rooms'].unique())
        with f3:
            max_price = st.slider("最高月租 (£)", 1000, 15000, 15000)

    # 应用过滤逻辑
    mask = (df['region'].isin(sel_region)) & (df['rooms'].isin(sel_rooms)) & (df['price'] <= max_price)
    filtered_df = df[mask]

    # 排序：精选置顶
    if 'is_featured' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])
    else:
        filtered_df = filtered_df.sort_values(by='date', ascending=False)

    # 渲染房源卡片
    cols = st.columns(3)
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                # 精选标签
                if row.get('is_featured', False):
                    st.markdown('<p style="background:#ff4b4b; color:white; padding:2px 8px; border-radius:3px; font-size:12px; width:fit-content;">🌟 FEATURED</p>', unsafe_allow_html=True)
                
                st.image(row['poster-link'], use_container_width=True)
                st.write(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | {row['rooms']} | £{row['price']}")
                
                if st.button("查看详情", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
except:
    st.error("房源加载中...")
