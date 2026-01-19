import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
import requests  # <-- 核心修复：必须导入这个库才能下载海报
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 增强型 CSS 样式 ---
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
        justify-content: flex-start;
        padding: 5px 20px;
        height: 70px;
        border-bottom: 1px solid #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .logo-img { max-height: 40px; width: auto; margin-right: 15px; }
    .header-text { border-left: 1px solid #ddd; padding-left: 15px; }
    .header-title { font-family: 'Times New Roman', serif; font-size: 18px; font-weight: bold; color: #1a1a1a; margin: 0; }
    .header-subtitle { font-size: 9px; color: #888; letter-spacing: 2px; margin: 0; }
    
    .stImage > img { border-radius: 12px; }
    .meta-row { display: flex; justify-content: space-between; align-items: center; margin-top: 5px; }
    .date-label { color: #888; font-size: 11px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 收藏功能逻辑 ---
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

def toggle_fav(title):
    if title in st.session_state.favorites:
        st.session_state.favorites.remove(title)
    else:
        st.session_state.favorites.append(title)

# --- 4. 详情弹窗 (微信改为一键复制模式，保持 WhatsApp 和 拨号) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    
    st.markdown(f"📅 **起租日期/发布**: {item['date']}")
    st.markdown("### 📋 房源亮点")
    st.write(item['description'])
    st.divider()
    
    # 联系人配置
    wechat_id = "HaoHarbour_UK"
    phone_num = "447450912493" # 确保此处为您接听咨询的真实号码
    
    st.markdown("💬 **立即咨询 Hao Harbour**")
    
    # 1. 微信区域 (置顶并强化复制体验)
    with st.container(border=True):
        st.markdown(f"✨ **微信咨询：点击下方 ID 即可复制**")
        # st.code 在手机端点一下通常会自动全选，非常方便用户复制
        st.code(wechat_id, language=None)
        st.caption("提示：复制后打开微信，在搜索框粘贴即可添加好友。")

    # 2. WhatsApp & 拨号 (保持并排)
    c1, c2 = st.columns(2)
    with c1:
        wa_msg = f"您好，我想咨询房源：{item['title']} (租金 £{item['price']})"
        wa_url = f"https://wa.me/{phone_num}?text={wa_msg}"
        st.markdown(f'''
            <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:45px; border-radius:10px; border:none; background:#25D366; color:white; font-weight:bold; cursor:pointer;">
                    WhatsApp 咨询
                </button>
            </a>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <a href="tel:+{phone_num}" style="text-decoration:none;">
                <button style="width:100%; height:45px; border-radius:10px; border:1px solid #25D366; background:white; color:#25D366; font-weight:bold; cursor:pointer;">
                    📞 拨打热线
                </button>
            </a>
        ''', unsafe_allow_html=True)

    st.divider()

    # 3. 分享与海报下载 (已包含 requests 修复)
    st.markdown("🔗 **分享此房源**")
    try:
        img_data = requests.get(item['poster-link']).content
        st.download_button(
            label="🖼️ 下载精美海报 (可发朋友圈/转发)",
            data=img_data,
            file_name=f"HaoHarbour_{item['title']}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )
    except:
        st.write("海报预览中...")

    # 文字分享
    share_msg = f"Hao Harbour 房源推荐：\n🏠 {item['title']}\n💰 £{int(item['price']):,}/pcm\n✨ {item['description']}\n💬 微信: {wechat_id}"
    st.code(share_msg, language=None)

# --- 5. 渲染 Header ---
logo_file = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
if os.path.exists(logo_file):
    with open(logo_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <div class="custom-header">
            <img src="data:image/png;base64,{data}" class="logo-img">
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">EXCLUSIVE LONDON LIVING</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. 获取数据 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
    df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values(by='date_dt', ascending=False).drop(columns=['date_dt'])
except Exception:
    st.info("🏠 正在为您加载最新房源...")
    st.stop()

# --- 7. 手机端筛选器 ---
with st.expander("🔍 筛选房源 / 收藏夹", expanded=False):
    t_a, t_b = st.tabs(["全部筛选", "❤️ 我的收藏"])
    with t_a:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
        with c2: f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
        with c3:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            f_price = st.slider("最高预算", 0, int(df['price'].max())+500, int(df['price'].max()))
    with t_b:
        show_fav = st.checkbox("仅看我收藏的")

filtered = df.copy()
if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
filtered = filtered[filtered['price'] <= f_price]
if 'show_fav' in locals() and show_fav: filtered = filtered[filtered['title'].isin(st.session_state.favorites)]

# --- 8. 房源展示 ---
st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")
if not filtered.empty:
    m_cols = st.columns(3)
    for i, (idx, row) in enumerate(filtered.iterrows()):
        with m_cols[i % 3]:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                tc1, tc2 = st.columns([4, 1])
                with tc1: st.markdown(f"**{row['title']}**")
                with tc2:
                    fav_icon = "❤️" if row['title'] in st.session_state.favorites else "🤍"
                    st.button(fav_icon, key=f"f_{idx}", on_click=toggle_fav, args=(row['title'],))
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.markdown(f"""<div class="meta-row"><span class="date-label">📅 {row['date']}</span>
                    <span style="color:#ff4b4b; font-weight:bold; font-size:18px;">£{int(row['price']):,}</span></div>""", unsafe_allow_html=True)
                if st.button("查看详情 & 联系", key=f"b_{idx}", use_container_width=True):
                    show_details(row)
else:
    st.warning("暂无房源。")

st.divider()
st.caption("© 2026 Hao Harbour Properties.")
