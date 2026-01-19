import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
import requests

# --- 1. 基础配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# 初始化收藏夹逻辑 (防止报错)
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

def toggle_fav(title):
    if title in st.session_state.favorites:
        st.session_state.favorites.remove(title)
    else:
        st.session_state.favorites.append(title)

# --- 2. 精简 CSS 样式 (保持你最满意的样子) ---
st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: -45px; }
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .custom-header {
        background-color: #ffffff;
        display: flex;
        align-items: center;
        padding: 5px 20px;
        height: 70px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 20px;
    }
    .logo-img { max-height: 40px; margin-right: 15px; }
    .header-text { border-left: 1px solid #ddd; padding-left: 15px; }
    .header-title { font-family: sans-serif; font-size: 18px; font-weight: bold; color: #1a1a1a; margin: 0; }
    .header-subtitle { font-size: 9px; color: #888; letter-spacing: 2px; margin: 0; }
    
    .stImage > img { border-radius: 12px; }
    .meta-row { display: flex; justify-content: space-between; align-items: center; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 详情弹窗 (地图 + 微信复制 + WhatsApp + 拨号 + 房源描述复制) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    
    # 地图跳转逻辑
    map_query = f"{item['title']}, London".replace(" ", "+")
    map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
    
    c_date, c_map = st.columns([2, 1])
    with c_date:
        st.markdown(f"📅 **发布日期**: {item['date']}")
    with c_map:
        st.markdown(f'''
            <a href="{map_url}" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:32px; border-radius:6px; border:1px solid #ff4b4b; background:white; color:#ff4b4b; font-size:12px; font-weight:bold; cursor:pointer;">
                    📍 地图找房
                </button>
            </a>
        ''', unsafe_allow_html=True)

    st.markdown("### 📋 房源亮点")
    st.write(item['description'])
    st.divider()
    
    # 联系配置
    wechat_id = "HaoHarbour_UK"
    phone_num = "447000000000" 
    
    st.markdown("💬 **立即咨询**")
    
    # 微信区
    with st.container(border=True):
        st.markdown(f"✨ **微信 ID (点击即可复制):**")
        st.code(wechat_id, language=None)
        st.caption("复制后在微信搜索添加即可")

    # WhatsApp & 拨号
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        wa_url = f"https://wa.me/{phone_num}?text=您好，咨询房源：{item['title']}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; border:none; background:#25D366; color:white; font-weight:bold; cursor:pointer; width:100%;">WhatsApp</button></a>', unsafe_allow_html=True)
    with btn_col2:
        st.markdown(f'<a href="tel:+{phone_num}"><button style="width:100%; height:45px; border-radius:10px; border:1px solid #25D366; background:white; color:#25D366; font-weight:bold; cursor:pointer; width:100%;">📞 拨号</button></a>', unsafe_allow_html=True)

    st.divider()

    # --- 分享区域：海报下载 + 描述复制 ---
    st.markdown("🔗 **分享此房源**")
    
    # 1. 下载海报按钮
    try:
        img_data = requests.get(item['poster-link'], timeout=5).content
        st.download_button(
            label="🖼️ 下载精美海报", 
            data=img_data, 
            file_name=f"{item['title']}_HaoHarbour.jpg", 
            mime="image/jpeg", 
            use_container_width=True
        )
    except:
        st.caption("海报生成中...")

    # 2. 一键复制描述 (加回来的功能)
    st.write("📋 **点击下方文字即可全选复制描述:**")
    share_text = (
        f"🏠 Hao Harbour 房源推荐：{item['title']}\n"
        f"💰 租金：£{int(item['price']):,}/pcm\n"
        f"📍 区域：{item['region']}\n"
        f"✨ 亮点：{item['description']}\n"
        f"💬 咨询微信：{wechat_id}"
    )
    st.code(share_text, language=None)

# --- 4. 渲染 Header ---
logo_file = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
if os.path.exists(logo_file):
    with open(logo_file, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{logo_data}" class="logo-img">
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">EXCLUSIVE LONDON LIVING</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 5. 获取数据 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
    df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values(by='date_dt', ascending=False).drop(columns=['date_dt'])
except Exception:
    st.info("🏠 正在为您加载最新房源...")
    st.stop()

# --- 6. 筛选布局 ---
with st.expander("🔍 筛选房源 / 收藏夹", expanded=False):
    t1, t2 = st.tabs(["全部筛选", "❤️ 我的收藏"])
    with t1:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
        with c2: f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
        with c3:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            f_price = st.slider("最高预算", 0, int(df['price'].max())+500, int(df['price'].max()))
    with t2:
        show_fav_only = st.checkbox("仅查看收藏房源")

# 过滤逻辑
filtered_df = df.copy()
if f_reg: filtered_df = filtered_df[filtered_df['region'].isin(f_reg)]
if f_rm: filtered_df = filtered_df[filtered_df['rooms'].isin(f_rm)]
filtered_df = filtered_df[filtered_df['price'] <= f_price]
if show_fav_only:
    filtered_df = filtered_df[filtered_df['title'].isin(st.session_state.favorites)]

# --- 7. 房源展示 ---
# --- 在 show_details 函数内部开头加入逻辑 ---
@st.dialog("房源详情")
def show_details(item):
    # 增加浏览量逻辑
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 读取最新数据
        full_df = conn.read(worksheet="Sheet1", ttl=0)
        
        # 找到当前房源所在的行，并在 views 列加 1
        # 注意：这里假设 title 是唯一的
        if 'views' in full_df.columns:
            full_df.loc[full_df['title'] == item['title'], 'views'] += 1
            conn.update(worksheet="Sheet1", data=full_df)
    except Exception as e:
        print(f"Views update failed: {e}")

    # ... 剩下的展示代码保持不变 ...
    st.image(item['poster-link'], use_container_width=True)
st.markdown(f"#### 📍 发现 {len(filtered_df)} 套精品房源")
if not filtered_df.empty:
    m_cols = st.columns(3)
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        with m_cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                title_c1, title_c2 = st.columns([4, 1])
                with title_c1: st.markdown(f"**{row['title']}**")
                with title_c2:
                    icon = "❤️" if row['title'] in st.session_state.favorites else "🤍"
                    st.button(icon, key=f"f_{idx}", on_click=toggle_fav, args=(row['title'],))
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.markdown(f"""<div class="meta-row"><span class="date-label">📅 {row['date']}</span>
                    <span style="color:#ff4b4b; font-weight:bold; font-size:18px;">£{int(row['price']):,}</span></div>""", unsafe_allow_html=True)
                if st.button("查看详情 & 联系", key=f"b_{idx}", use_container_width=True):
                    show_details(row)
else:
    st.warning("暂无房源。")

st.divider()
st.caption("© 2026 Hao Harbour Properties.")
