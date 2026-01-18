import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 页面配置与 CSS 优化 ---
st.set_page_config(page_title="Hao Harbour | 伦敦房源精选", layout="wide")

# 强制优化顶部 Banner 大小，解决你之前提到的遮挡问题
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
    }
    .stAppViewMain img {
        border-radius: 10px;
    }
    /* 限制 Banner 高度 */
    .banner-container {
        width: 100%;
        height: 250px;
        overflow: hidden;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .banner-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 加载 Banner ---
# 建议在 GitHub 仓库放一个 banner.png
try:
    st.markdown('<div class="banner-container"><img src="https://raw.githubusercontent.com/你的用户名/你的仓库名/main/banner.png" class="banner-img"></div>', unsafe_allow_html=True)
except:
    st.title("🏡 Hao Harbour | 伦敦精品房源")

# --- 3. 连接数据源 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 强制读取最新数据，不使用缓存，确保 Admin 发布后这里立刻更新
    df = conn.read(worksheet="Sheet1", ttl=0)
    # 清理掉表格中的全空行，防止索引崩溃
    df = df.dropna(subset=['title', 'poster-link'])
except Exception as e:
    st.error(f"数据加载失败，请联系管理员。详情: {e}")
    st.stop()

# --- 4. 侧边栏筛选器 ---
st.sidebar.header("🔍 房源筛选")
selected_region = st.sidebar.multiselect("区域", options=df['region'].unique())
max_price = st.sidebar.slider("最高预算 (£/pcm)", 
                              min_value=0, 
                              max_value=int(df['price'].max()) if not df.empty else 10000, 
                              value=int(df['price'].max()) if not df.empty else 10000)

# 过滤逻辑
filtered_df = df.copy()
if selected_region:
    filtered_df = filtered_df[filtered_df['region'].isin(selected_region)]
filtered_df = filtered_df[filtered_df['price'] <= max_price]

# --- 5. 房源展示展厅 ---
if filtered_df.empty:
    st.info("⚠️ 暂无符合条件的房源，请调整筛选条件。")
else:
    # 使用三列布局
    cols = st.columns(3)
    
    for idx, row in filtered_df.iterrows():
        with cols[idx % 3]:
            # 使用 container 包裹，增加边框美感
            with st.container(border=True):
                # --- 关键防崩溃逻辑：图片链接检查 ---
                img_url = row.get('poster-link')
                if pd.isna(img_url) or str(img_url).strip() == "":
                    # 如果链接为空，显示占位图
                    st.image("https://via.placeholder.com/400x550?text=Hao+Harbour", use_container_width=True)
                else:
                    # 只有链接存在才渲染图片
                    st.image(img_url, use_container_width=True)
                
                st.subheader(f"{row['title']}")
                st.write(f"📍 区域: {row['region']} | 🛏️ 房型: {row['rooms']}")
                st.markdown(f"### **£{row['price']:,} /pcm**")
                
                # --- 详情弹窗 ---
                if st.button(f"查看详情", key=f"btn_{idx}"):
                    @st.dialog(f"房源详情: {row['title']}")
                    def show_details(item):
                        st.image(item['poster-link'])
                        st.markdown("### 📋 房源亮点")
                        # 显示 DeepSeek 生成的打钩描述
                        st.write(item['description'])
                        st.divider()
                        st.markdown("💬 **联系我们获取更多信息或看房预约**")
                        st.write("微信客服: HaoHarbour_UK")
                    
                    show_details(row)

# --- 6. 底部版权 ---
st.divider()
st.caption("© 2026 Hao Harbour Properties. All Rights Reserved.")
