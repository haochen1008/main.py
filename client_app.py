import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse

# --- 1. 彻底隐藏右上角图标与装饰 ---
st.set_page_config(page_title="Hao Harbour | Exclusive London Living", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stToolbar"] {display: none !important;}
    /* 隐藏筛选器展开后的默认白边 */
    .st-expander {border: none !important; box-shadow: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗函数 (保留所有交互) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    st.write(f"💰 **Monthly Rent: £{item['price']}**")
    st.markdown(item.get('description', '暂无详细说明'))
    st.divider()

    # 咨询工具栏
    c1, c2, c3 = st.columns(3)
    with c1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("微信 ID (点击复制)")
    with c2:
        phone = "447000000000" # 记得改成你的号码
        wa_url = f"https://wa.me/{phone}?text=" + urllib.parse.quote(f"Hi, I'm interested in {item['title']}")
        st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
    with c3:
        st.link_button("📞 拨打电话", f"tel:+{phone}", use_container_width=True)

    c4, c5 = st.columns(2)
    with c4:
        map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(item['title'] + ', London')}"
        st.link_button("📍 Google Maps", map_url, use_container_width=True)
    with c5:
        try:
            img_data = requests.get(item['poster-link']).content
            st.download_button("📥 下载海报", data=img_data, file_name=f"{item['title']}.jpg", use_container_width=True)
        except: pass

    # 后台浏览量加 1
    try:
        conn_u = st.connection("gsheets", type=GSheetsConnection)
        df_u = conn_u.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_u.columns:
            df_u.loc[df_u['title'] == item['title'], 'views'] += 1
            conn_u.update(worksheet="Sheet1", data=df_u)
    except: pass

# --- 3. 顶部 Logo 与 品牌展示 ---
# 建议：如果 Logo 还在报错，请确保 logo.png 文件放在 admin_app.py 同级目录下
try:
    col_logo_1, col_logo_2, col_logo_3 = st.columns([2, 1, 2])
    with col_logo_2:
        # 这里尝试加载本地 logo.png，如果不存在则显示文字
        st.image("logo.png", width=150) 
except:
    st.markdown("<h1 style='text-align: center; color: #bfa064;'>HAO HARBOUR</h1>", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; margin-top: -20px; margin-bottom: 20px;">
        <p style="color: #bfa064; font-weight: bold; letter-spacing: 3px; font-size: 14px;">EXCLUSIVE LONDON LIVING</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. 数据加载与下拉折叠筛选器 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')

    # 改为 st.expander (下拉式筛选)，默认 expanded=False 即不打开
    with st.expander("🔍 筛选房源 (Filter Properties)", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            all_regions = df['region'].unique().tolist()
            sel_region = st.multiselect("区域 (Region)", options=all_regions, default=all_regions)
        with f2:
            all_rooms = df['rooms'].unique().tolist()
            sel_rooms = st.multiselect("房型 (Room Type)", options=all_rooms, default=all_rooms)
        with f3:
            max_p = int(df['price'].max()) if not df.empty else 15000
            sel_price = st.slider("最高月租 (£)", 1000, max_p, max_p)

    # 过滤逻辑
    filtered_df = df[
        (df['region'].isin(sel_region)) & 
        (df['rooms'].isin(sel_rooms)) & 
        (df['price'] <= sel_price)
    ]

    # 排序：精选优先
    if 'is_featured' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])
    else:
        filtered_df = filtered_df.sort_values(by='date', ascending=False)

    # --- 5. 房源矩阵展示 ---
    if filtered_df.empty:
        st.info("没有找到符合条件的房源，请调整筛选条件。")
    else:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(filtered_df.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    if row.get('is_featured', False):
                        st.markdown('<p style="background:#ff4b4b; color:white; padding:2px 8px; border-radius:3px; font-size:11px; width:fit-content; margin-bottom:5px;">🌟 FEATURED</p>', unsafe_allow_html=True)
                    
                    st.image(row['poster-link'], use_container_width=True)
                    st.markdown(f"**{row['title']}**")
                    st.caption(f"📍 {row['region']} | {row['rooms']} | £{row['price']}/pcm")
                    
                    if st.button("View Details", key=f"btn_{idx}", use_container_width=True):
                        show_details(row)
except Exception as e:
    st.error(f"加载异常，请稍后刷新。")
