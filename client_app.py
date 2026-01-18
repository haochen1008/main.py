import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 页面配置与视觉优化 ---
st.set_page_config(page_title="Hao Harbour | London Excellence", layout="wide")

# 核心 CSS：消除顶部白边，并让 Logo 和 Banner 优雅并排
st.markdown("""
    <style>
    /* 消除顶部默认间距 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 品牌头部容器：Logo 和 Banner 横向排布 */
    .header-container {
        display: flex;
        align-items: center; /* 垂直居中 */
        gap: 20px;           /* 两者间距 */
        padding: 15px 0;
        background-color: white;
    }
    
    .logo-img {
        height: 80px;        /* 限制 Logo 高度，防止变成大白块 */
        object-fit: contain;
    }
    
    .banner-img {
        flex-grow: 1;        /* Banner 占据剩余空间 */
        height: 120px;       /* 限制 Banner 高度 */
        object-fit: cover;   /* 裁剪填充，不拉伸变形 */
        border-radius: 10px;
    }
    
    /* 房源卡片样式 */
    .stImage > img {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 品牌元素 (Logo + Banner 并排) ---
# 注意：确保 GitHub 仓库中有 logo.jpg 和 banner.png，或者替换为你的图片链接
st.markdown(f"""
    <div class="header-container">
        <img src="https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USER', 'yourname')}/{st.secrets.get('GITHUB_REPO', 'yourrepo')}/main/logo.jpg" class="logo-img">
        <img src="https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USER', 'yourname')}/{st.secrets.get('GITHUB_REPO', 'yourrepo')}/main/banner.png" class="banner-img">
    </div>
""", unsafe_allow_html=True)

# --- 3. 连接数据源 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    # 彻底清理空行，防止崩溃
    df = df.dropna(subset=['title', 'poster-link'])
except Exception as e:
    st.error("正在加载精选房源...")
    st.stop()

# --- 4. 侧边栏筛选 (保留你要求的房型筛选) ---
st.sidebar.markdown("## 🔍 房源筛选")

with st.sidebar:
    # 区域多选
    all_regions = df['region'].unique().tolist()
    selected_region = st.multiselect("选择区域", options=all_regions)

    # 房型多选 (找回房型)
    all_rooms = df['rooms'].unique().tolist()
    selected_rooms = st.multiselect("选择房型", options=all_rooms)

    # 价格滑动条
    max_p = int(df['price'].max()) if not df.empty else 10000
    price_limit = st.sidebar.slider("最高月租 (£/pcm)", 0, max_p, max_p)

# 执行过滤逻辑
filtered = df.copy()
if selected_region:
    filtered = filtered[filtered['region'].isin(selected_region)]
if selected_rooms:
    filtered = filtered[filtered['rooms'].isin(selected_rooms)]
filtered = filtered[filtered['price'] <= price_limit]

# --- 5. 房源展示 ---
st.markdown(f"### 📍 发现 {len(filtered)} 套精品房源")

if filtered.empty:
    st.info("房源库正在更新中...")
else:
    # 保持三列布局
    grid_cols = st.columns(3)
    
    for i, (_, row) in enumerate(filtered.iterrows()):
        with grid_cols[i % 3]:
            with st.container(border=True):
                # 图片渲染及防错处理
                img_url = row['poster-link']
                if pd.isna(img_url) or str(img_url).strip() == "":
                    st.image("https://via.placeholder.com/400x500?text=Hao+Harbour", use_container_width=True)
                else:
                    st.image(img_url, use_container_width=True)
                
                # 文字信息
                st.markdown(f"**{row['title']}**")
                st.markdown(f"**{row['rooms']}** | {row['region']}")
                st.markdown(f"#### **£{row['price']:,} /pcm**")
                
                # 查看详情弹窗
                if st.button("查看详情", key=f"view_{i}"):
                    @st.dialog(f"{row['title']}")
                    def show_info(data):
                        st.image(data['poster-link'], use_container_width=True)
                        st.markdown("### 📋 房源亮点")
                        # 完美适配 DeepSeek 生成的打钩格式
                        st.write(data['description'])
                        st.divider()
                        st.markdown("💬 **联系我们看房**")
                        st.markdown("WeChat: HaoHarbour_UK")
                    
                    show_info(row)

# --- 6. 底部 ---
st.divider()
st.caption("© 2026 Hao Harbour Properties. All Rights Reserved.")
