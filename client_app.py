import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 增强型 CSS (保留原有样式，新增收藏/日期样式) ---
st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: -45px; }
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 极简 Header */
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
    
    /* 房源卡片圆角 */
    .stImage > img { border-radius: 12px; }
    
    /* 日期与收藏样式 */
    .meta-row { display: flex; justify-content: space-between; align-items: center; margin-top: 5px; }
    .date-label { color: #888; font-size: 11px; }
    
    /* 按钮样式优化 */
    div.stButton > button { border-radius: 8px; }
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

# --- 4. 详情弹窗 (新增电话直达与分享) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"📅 **起租日期/发布**: {item['date']}")
    with c2:
        # 简单的分享文本
        share_text = f"推荐一套伦敦房源：{item['title']}，租金 £{item['price']}/pcm。详情请查看官网。"
        st.button("📋 复制分享语", on_click=lambda: st.toast("分享语已准备好，长按复制！"))

    st.markdown("### 📋 房源亮点")
    st.write(item['description'])
    st.divider()
    
    st.markdown("💬 **联系我们获取详细资料**")
    col_a, col_b = st.columns(2)
    with col_a:
        # 这里修改为你真实的电话，手机点击可直接拨打
        st.markdown('<a href="tel:+447450912493" style="text-decoration:none;"><button style="width:100%; height:40px; border-radius:8px; border:1px solid #ddd; background:white;">📞 拨打电话</button></a>', unsafe_allow_html=True)
    with col_b:
        if os.path.exists("wechat_qr.png"):
            st.image("wechat_qr.png", caption="扫码加微信", width=150)
        else:
            st.info("微信客服: HaoHarbour_UK")

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

# --- 6. 数据处理 (新增自动排序) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
    
    # 日期转换并排序：最新的排在前面
    df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values(by='date_dt', ascending=False).drop(columns=['date_dt'])
except Exception:
    st.info("🏠 正在为您加载最新房源...")
    st.stop()

# --- 7. 手机端友好筛选器 (Expander) ---
with st.expander("🔍 筛选房源 / 收藏夹", expanded=False):
    tab1, tab2 = st.tabs(["全部筛选", "❤️ 我的收藏"])
    
    with tab1:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            f_reg = st.multiselect("区域", options=df['region'].unique().tolist())
        with c2:
            f_rm = st.multiselect("房型", options=df['rooms'].unique().tolist())
        with c3:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            max_p = int(df['price'].max()) if not df.empty else 10000
            f_price = st.slider("最高预算", 0, max_p + 500, max_p)
    
    with tab2:
        show_fav_only = st.checkbox("仅显示我收藏的房源")

# 过滤逻辑
filtered = df.copy()
if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
filtered = filtered[filtered['price'] <= f_price]
if 'show_fav_only' in locals() and show_fav_only:
    filtered = filtered[filtered['title'].isin(st.session_state.favorites)]

# --- 8. 房源展示 (自适应列) ---
st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")

if not filtered.empty:
    main_cols = st.columns(3) # 电脑端3列，手机端自动变1列
    for i, (idx, row) in enumerate(filtered.iterrows()):
        col_to_use = main_cols[i % 3]
        with col_to_use:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                
                # 标题与收藏按钮
                t1, t2 = st.columns([4, 1])
                with t1:
                    st.markdown(f"**{row['title']}**")
                with t2:
                    is_fav = "❤️" if row['title'] in st.session_state.favorites else "🤍"
                    st.button(is_fav, key=f"fav_{idx}", on_click=toggle_fav, args=(row['title'],))
                
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                
                # 日期与价格行
                st.markdown(f"""
                    <div class="meta-row">
                        <span class="date-label">📅 {row['date']}</span>
                        <span style="color:#ff4b4b; font-weight:bold; font-size:18px;">£{int(row['price']):,} /pcm</span>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("查看详情 & 联系", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
else:
    st.warning("没有找到符合条件的房源。")

st.divider()
st.caption("© 2026 Hao Harbour Properties. All rights reserved.")
