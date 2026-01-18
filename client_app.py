import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="Hao Harbour | 伦敦房源精选", layout="wide")

# --- 2. 核心样式表 (CSS) ---
# 这里控制了 Banner 的高度 (180px) 和 按钮的颜色
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 强制横幅比例，防止过大 */
    .banner-box {
        width: 100%;
        height: 180px; /* 这里可以微调高度，数值越小越窄 */
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .banner-box img {
        width: 100%;
        height: 100%;
        object-fit: cover; /* 自动剪裁图片以填充框格 */
        object-position: center;
    }
    
    /* 按钮颜色微调（深蓝/金色系） */
    .stButton>button {
        border-radius: 5px;
        border: 1px solid #d4af37;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 顶部 Banner (使用 HTML 容器确保尺寸固定) ---
try:
    # 检查目录下是否有 banner.png
    import os
    if os.path.exists("banner.png"):
        st.markdown('<div class="banner-box"><img src="app/static/banner.png"></div>', unsafe_allow_html=True)
    else:
        # 如果没找到图，显示备用文字标题
        st.markdown("<h1 style='text-align: center;'>🏡 Hao Harbour | 伦敦房源精选</h1>", unsafe_allow_html=True)
except:
    st.title("🏡 Hao Harbour | 伦敦房源精选")

# --- 4. 连接数据库 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300)
except Exception as e:
    st.error("数据连接中，请刷新页面...")
    st.stop()

# --- 5. 侧边栏筛选器 ---
if not df.empty:
    with st.sidebar:
        st.markdown("### 🔍 房源筛选")
        f_reg = st.multiselect("选择区域", options=df['region'].unique().tolist())
        f_rm = st.multiselect("选择房型", options=df['rooms'].unique().tolist())
        
        # 价格滑块
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
        # 使用 3 列布局
        cols = st.columns(3)
        for idx, row in filtered.iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    # 图片展示
                    st.image(row['poster_link'], use_container_width=True)
                    st.markdown(f"### {row['title']}")
                    st.write(f"📍 {row['region']} | 🏠 {row['rooms']}")
                    st.markdown(f"#### :red[£{row['price']} /pcm]")
                    
                    # 弹窗功能
                    @st.dialog("联系 Hao Harbour 专属顾问")
                    def show_contact(prop_name):
                        st.write(f"您正在咨询：**{prop_name}**")
                        if os.path.exists("wechat_qr.png"):
                            st.image("wechat_qr.png", caption="扫码添加经纪人微信")
                        else:
                            st.warning("微信二维码图片 (wechat_qr.png) 尚未上传")
                        st.info("💡 请备注：咨询 " + prop_name)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("📄 查看大图", row['poster_link'], use_container_width=True)
                    with c2:
                        if st.button("💬 立即咨询", key=f"btn_{idx}", use_container_width=True):
                            show_contact(row['title'])
    else:
        st.info("没有找到匹配的房源，请尝试调整筛选条件。")
else:
    st.info("房源库正在更新中...")
