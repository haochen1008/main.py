import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 基础配置 ---
st.set_page_config(page_title="Hao Harbour 精选房源橱窗", layout="wide")

# 隐藏 Streamlit 默认的菜单和页脚，让它更像官网
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- 2. 云端连接 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=600) # 客户版可以设置缓存10分钟(600秒)提高加载速度
except Exception as e:
    st.error("数据加载中，请稍后再试...")
    st.stop()

# --- 3. 客户界面 ---
st.title("🏡 Hao Harbour | 伦敦房源精选")
st.markdown("---")

if not df.empty:
    # 侧边栏筛选（客户只能筛选，不能修改）
    with st.sidebar:
        st.header("🔍 寻找您的理想居所")
        f_reg = st.multiselect("区域位置", options=df['region'].unique())
        f_rm = st.multiselect("房型选择", options=df['rooms'].unique())
        max_p = int(df['price'].max())
        f_price = st.slider("最高预算 (£/pcm)", 0, max_p + 500, max_p + 500)

    # 执行筛选
    filtered = df
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # 画廊展示
    if not filtered.empty:
        cols = st.columns(3)
        for idx, row in filtered.iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    # 展示海报缩略图
                    st.image(row['poster_link'], use_container_width=True)
                    st.subheader(row['title'])
                    st.write(f"📍 {row['region']} | 🏠 {row['rooms']}")
                    st.write(f"💰 **£{row['price']} /pcm**")
                    
                    # 客户互动按钮
                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("📄 查看详情", row['poster_link'], use_container_width=True)
                    with c2:
                        # 这里可以换成你的 WhatsApp 或 微信二维码链接
                        st.link_button("💬 立即咨询", "https://wa.me/你的电话", use_container_width=True)
    else:
        st.info("暂无符合条件的房源，请调整筛选条件。")
else:
    st.info("敬请期待，精选房源即将更新...")
