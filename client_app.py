import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="Hao Harbour | 伦敦房源精选", layout="wide")

# --- 2. 核心样式表 (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 调整容器边距，让 Banner 更贴合顶部 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    /* 按钮颜色微调（深蓝/金色系） */
    .stButton>button {
        border-radius: 5px;
        border: 1px solid #d4af37;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 顶部 Banner 区域 ---
# 使用 st.columns 来控制 Banner 的宽度比例，或者直接居中显示
if os.path.exists("banner.png"):
    # 这里的 use_container_width=True 会自动适应页面宽度
    # 因为图片本身就是窄长的，所以它不会占据太多纵向高度
    st.image("banner.png", use_container_width=True)
else:
    st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

st.divider()

# --- 4. 连接数据库 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300)
except Exception as e:
    st.error("正在连接数据库，请稍候...")
    st.stop()

# --- 5. 侧边栏筛选器 ---
if not df.empty:
    with st.sidebar:
        st.markdown("### 🔍 房源筛选")
        f_reg = st.multiselect("选择区域", options=df['region'].unique().tolist())
        f_rm = st.multiselect("选择房型", options=df['rooms'].unique().tolist())
        
        # 价格滑块逻辑
        prices = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        max_p = int(prices.max())
        f_price = st.slider("最高月租 (£/pcm)", 0, max_p + 500, max_p + 500)

    # 过滤逻辑
    filtered = df.copy()
    filtered['price'] = pd.to_numeric(filtered['price'], errors='coerce')
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # --- 6. 房源橱窗展示 ---
    if not filtered.empty:
        cols = st.columns(3)
        for idx, row in filtered.iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    # 房源图片
                    st.image(row['poster_link'], use_container_width=True)
                    st.markdown(f"### {row['title']}")
                    st.write(f"📍 {row['region']} | 🏠 {row['rooms']}")
                    st.markdown(f"#### :red[£{row['price']} /pcm]")
                    
                    # 弹窗功能
                    @st.dialog("联系 Hao Harbour 专属顾问")
                    def show_contact(prop_name):
                        st.write(f"您正在咨询：**{prop_name}**")
                        if os.path.exists("wechat_qr.png"):
                            st.image("wechat_qr.png", caption="扫码添加微信")
                        else:
                            st.warning("请在仓库中上传 wechat_qr.png")
                        st.info("💡 建议备注：咨询 " + prop_name)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("📄 查看大图", row['poster_link'], use_container_width=True)
                    with c2:
                        if st.button("💬 立即咨询", key=f"btn_{idx}", use_container_width=True):
                            show_contact(row['title'])
    else:
        st.info("没有找到匹配的房源。")
else:
    st.info("房源库正在努力更新中...")
