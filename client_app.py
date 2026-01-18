import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | Exclusive London Living", layout="wide")

# 自定义样式：控制 Logo 和 Banner 间距
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem; }
    .stImage > img { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 品牌元素展示 (Banner & Logo) ---
col_logo, col_empty = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo.jpg", width=150) # 确保 GitHub 根目录有 logo.jpg
    except:
        st.subheader("Hao Harbour")

# 展示顶部的横幅 Banner
try:
    st.image("banner.png", use_container_width=True) # 确保 GitHub 根目录有 banner.png
except:
    pass

# --- 3. 获取数据 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 确保每次刷新都能看到 Admin 刚发出的 DeepSeek 描述
    df = conn.read(worksheet="Sheet1", ttl=0)
    
    # 清理：只保留有标题和图片链接的行，防止客户端报错崩溃
    df = df.dropna(subset=['title', 'poster-link'])
except Exception as e:
    st.error(f"连接数据库失败: {e}")
    st.stop()

# --- 4. 侧边栏筛选 (找回房型筛选) ---
st.sidebar.title("🔍 房源筛选")

# 区域筛选
regions = df['region'].unique().tolist()
selected_region = st.sidebar.multiselect("选择区域", options=regions)

# 房型筛选 (找回这部分)
room_types = df['rooms'].unique().tolist()
selected_rooms = st.sidebar.multiselect("选择房型", options=room_types)

# 价格筛选
max_p = int(df['price'].max()) if not df.empty else 10000
price_limit = st.sidebar.slider("最高月租 (£/pcm)", 0, max_p, max_p)

# 执行数据过滤
filtered = df.copy()
if selected_region:
    filtered = filtered[filtered['region'].isin(selected_region)]
if selected_rooms:
    filtered = filtered[filtered['rooms'].isin(selected_rooms)]
filtered = filtered[filtered['price'] <= price_limit]

# --- 5. 房源展厅 ---
st.markdown(f"### 📍 发现 {len(filtered)} 套精选房源")

if filtered.empty:
    st.warning("没有找到符合条件的房源。")
else:
    # 三列排列
    display_cols = st.columns(3)
    
    for i, (_, row) in enumerate(filtered.iterrows()):
        with display_cols[i % 3]:
            with st.container(border=True):
                # 图片展示逻辑 (防崩溃)
                p_link = row['poster-link']
                if pd.isna(p_link) or str(p_link).strip() == "":
                    st.image("https://via.placeholder.com/400x500?text=Image+Updating", use_container_width=True)
                else:
                    st.image(p_link, use_container_width=True)
                
                # 基本信息
                st.markdown(f"**{row['title']}**")
                st.markdown(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.markdown(f"#### £{row['price']:,} /pcm")
                
                # 找回 Description 的弹窗显示
                if st.button("查看详情", key=f"details_{i}"):
                    @st.dialog(f"{row['title']}")
                    def modal(item):
                        st.image(item['poster-link'], use_container_width=True)
                        st.markdown("### 📋 房源亮点")
                        # 这里显示的是 DeepSeek 生成的带 ✔ 的描述
                        st.write(item['description']) 
                        st.divider()
                        st.markdown("💬 **联系我们获取更多信息**")
                        st.markdown("微信: HaoHarbour_UK")
                    
                    modal(row)

# --- 6. 底部 ---
st.divider()
st.caption("© 2026 Hao Harbour Properties - Exclusive London Living")
