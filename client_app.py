import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 增强型样式 ---
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
    
    /* 日期标签样式 */
    .date-label { color: #888; font-size: 12px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 弹窗函数 (增加日期显示) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.markdown(f"**📅 发布日期: {item['date']}**") # 弹窗显示日期
    st.markdown("### 📋 房源亮点")
    st.write(item['description'])
    st.divider()
    st.markdown("💬 **联系我们获取详细资料**")
    if os.path.exists("wechat_qr.png"):
        st.image("wechat_qr.png", width=200)
    else:
        st.write("微信客服: HaoHarbour_UK")

# --- 4. 渲染 Header ---
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

# --- 5. 获取数据 ---
# 在 client_app.py 的获取数据部分
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    df = df.dropna(subset=['title', 'poster-link'])
    
    # 新增：按日期倒序排列，让新房子置顶
    df['date'] = pd.to_datetime(df['date'], errors='coerce') # 转为日期格式
    df = df.sort_values(by='date', ascending=False) # 倒序排
    df['date'] = df['date'].dt.strftime('%Y-%m-%d') # 再转回字符串显示
except Exception:
    # ... 原有代码 ...
    st.info("🏠 正在为您加载最新房源...")
    st.stop()

# --- 6. 自适应筛选布局 ---
with st.expander("🔍 点击筛选房源 (区域/房型/预算)", expanded=False):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        f_reg = st.multiselect("选择区域", options=df['region'].unique().tolist())
    with c2:
        f_rm = st.multiselect("选择房型", options=df['rooms'].unique().tolist())
    with c3:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        max_p = int(df['price'].max()) if not df.empty else 10000
        f_price = st.slider("最高月租 (£)", 0, max_p + 500, max_p)

filtered = df.copy()
if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
filtered = filtered[filtered['price'] <= f_price]

# --- 7. 房源展示 ---
st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")

if not filtered.empty:
    main_cols = st.columns(3)
    for i, (idx, row) in enumerate(filtered.iterrows()):
        col_to_use = main_cols[i % 3]
        with col_to_use:
            with st.container(border=True):
                st.image(row['poster-link'], use_container_width=True)
                st.markdown(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                
                # 在此插入日期显示
                st.markdown(f"<div class='date-label'>📅 {row['date']}</div>", unsafe_allow_html=True)
                
                st.markdown(f"#### :red[£{int(row['price']):,} /pcm]")
                if st.button("查看详情 & 联系", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
else:
    st.warning("没有找到符合条件的房源。")

st.divider()
st.caption("© 2026 Hao Harbour Properties.")
