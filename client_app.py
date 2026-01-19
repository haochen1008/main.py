import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse
import base64

# --- 1. 彻底隐藏右上角图标与装饰 ---
st.set_page_config(page_title="Hao Harbour | London Excellence", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stToolbar"] {display: none !important;}
    /* 隐藏筛选器卡片的边框 */
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

    c1, c2, c3 = st.columns(3)
    with c1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("微信 ID (点击复制)")
    with c2:
        phone = "447000000000" 
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

    # 静默更新浏览量
    try:
        conn_u = st.connection("gsheets", type=GSheetsConnection)
        df_u = conn_u.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_u.columns:
            idx = df_u.index[df_u['title'] == item['title']].tolist()
            if idx:
                df_u.at[idx[0], 'views'] = int(df_u.at[idx[0], 'views']) + 1
                conn_u.update(worksheet="Sheet1", data=df_u)
    except: pass

# --- 3. 顶部 Logo (兼容性最好的写法) ---
def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

try:
    # 尝试读取同级目录下的 logo.png
    encoded_logo = get_image_base64("logo.png")
    st.markdown(f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{encoded_logo}" width="120">
        </div>
    """, unsafe_allow_html=True)
except:
    # 如果找不到文件，显示备用高清文字 Logo
    st.markdown("<h1 style='text-align: center; color: #bfa064; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #bfa064; font-weight: bold; letter-spacing: 3px; font-size: 14px; margin-top:0;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

# --- 4. 数据加载与折叠下拉筛选器 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')

    # 下拉筛选容器
    with st.expander("🔍 筛选房源 (Filter Properties)", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            # 这里的下拉框客户点击才会看到选项
            sel_region = st.multiselect("区域 (Region)", options=df['region'].unique().tolist(), placeholder="请选择区域")
        with f2:
            sel_rooms = st.multiselect("房型 (Room Type)", options=df['rooms'].unique().tolist(), placeholder="请选择房型")
        with f3:
            max_p = int(df['price'].max()) if not df.empty else 15000
            sel_price = st.slider("最高月租 (£)", 1000, max_p, max_p)

    # 逻辑过滤
    filtered_df = df.copy()
    if sel_region:
        filtered_df = filtered_df[filtered_df['region'].isin(sel_region)]
    if sel_rooms:
        filtered_df = filtered_df[filtered_df['rooms'].isin(sel_rooms)]
    filtered_df = filtered_df[filtered_df['price'] <= sel_price]

    # 精选置顶
    if 'is_featured' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])
    else:
        filtered_df = filtered_df.sort_values(by='date', ascending=False)

    # --- 5. 展示矩阵 ---
    if filtered_df.empty:
        st.info("没有找到符合条件的房源。")
    else:
        grid_cols = st.columns(3)
        for i, (idx, row) in enumerate(filtered_df.iterrows()):
            with grid_cols[i % 3]:
                with st.container(border=True):
                    if row.get('is_featured', False):
                        st.markdown('<div style="background:#ff4b4b; color:white; padding:2px 8px; border-radius:3px; font-size:11px; width:fit-content; margin-bottom:5px;">🌟 FEATURED</div>', unsafe_allow_html=True)
                    
                    st.image(row['poster-link'], use_container_width=True)
                    st.markdown(f"**{row['title']}**")
                    st.caption(f"📍 {row['region']} | {row['rooms']} | £{row['price']}/pcm")
                    
                    if st.button("View Details", key=f"btn_{idx}", use_container_width=True):
                        show_details(row)
except Exception as e:
    st.error("房源加载中...")
