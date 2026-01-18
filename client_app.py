import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="Hao Harbour | 伦敦房源精选", layout="wide")

# 隐藏多余 UI，增强品牌感
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #fcfcfc; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 顶部 Banner 区域 ---
# 将 banner.jpg 改为 banner.png
try:
    st.image("banner.png", use_container_width=True)
except:
    # 如果图片加载失败（比如还没上传），则显示默认标题
    st.title("🏡 Hao Harbour | 伦敦房源精选")

# --- 3. 连接数据库 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300) # 缓存5分钟
except Exception as e:
    st.error("数据加载中，请稍后再试...")
    st.stop()

# --- 4. 侧边栏筛选器 ---
if not df.empty:
    with st.sidebar:
        st.header("🔍 精确筛选")
        f_reg = st.multiselect("区域位置", options=df['region'].unique())
        f_rm = st.multiselect("房型选择", options=df['rooms'].unique())
        max_p = int(df['price'].max())
        f_price = st.slider("最高月租 (£/pcm)", 0, max_p + 500, max_p + 500)

    # 执行过滤逻辑
    filtered = df
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # --- 5. 房源橱窗展示 ---
    if not filtered.empty:
        cols = st.columns(3)
        for idx, row in filtered.iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    # 展示房源海报
                    st.image(row['poster_link'], use_container_width=True)
                    st.subheader(row['title'])
                    st.write(f"📍 {row['region']} | 🏠 {row['rooms']}")
                    st.markdown(f"#### :red[£{row['price']} /pcm]")
                    
                    # 定义弹窗功能：联系房产顾问
                    @st.dialog("联系 Hao Harbour 专属顾问")
                    def show_contact(prop_name):
                        st.write(f"您正在咨询房源：**{prop_name}**")
                        # 确保你的 GitHub 仓库里有名为 wechat_qr.png 的文件
                        st.image("wechat_qr.png", caption="长按扫码，添加经纪人微信")
                        st.info("💡 请备注：咨询 " + prop_name)

                    # 按钮行
                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("📄 查看大图", row['poster_link'], use_container_width=True)
                    with c2:
                        if st.button("💬 立即咨询", key=f"btn_{idx}", use_container_width=True):
                            show_contact(row['title'])
    else:
        st.info("暂无符合条件的房源。")
else:
    st.info("房源库更新中，敬请期待...")
