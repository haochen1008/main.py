import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 深度清理白边与极简 Header 样式 ---
st.markdown("""
    <style>
    /* 彻底消除顶部空白 */
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        margin-top: -45px; /* 进一步向上提拉，消除白边 */
    }
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 超窄白色横幅容器 */
    .custom-header {
        background-color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 5px 30px;
        height: 70px;
        border-bottom: 1px solid #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        height: 100%;
    }

    .logo-img {
        max-height: 45px;
        width: auto;
        margin-right: 25px;
    }
    
    .header-text {
        border-left: 1px solid #ddd;
        padding-left: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .header-title {
        font-family: 'Times New Roman', serif;
        font-size: 20px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 0;
        line-height: 1.2;
    }
    
    .header-subtitle {
        font-size: 10px;
        color: #888;
        letter-spacing: 3px;
        margin: 0;
        line-height: 1.2;
    }

    /* 房源图片圆角 */
    .stImage > img {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 渲染极简 Header ---
# 自动检测 logo.png 或 logo.jpg
logo_file = "logo.png" if os.path.exists("logo.png") else "logo.jpg"
if os.path.exists(logo_file):
    with open(logo_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
        <div class="custom-header">
            <div class="logo-container">
                <img src="data:image/png;base64,{data}" class="logo-img">
            </div>
            <div class="header-text">
                <p class="header-title">HAO HARBOUR</p>
                <p class="header-subtitle">EXCLUSIVE LONDON LIVING</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("### HAO HARBOUR | EXCLUSIVE LONDON LIVING")

# --- 4. 数据库连接 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 保证 DeepSeek 提取的最新内容实时更新
    df = conn.read(worksheet="Sheet1", ttl=0)
    # 过滤掉坏数据
    df = df.dropna(subset=['title', 'poster-link'])
except Exception as e:
    st.info("🏠 正在为您加载最新精品房源...")
    st.stop()

# --- 5. 侧边栏与过滤逻辑 ---
if not df.empty:
    with st.sidebar:
        st.markdown("### 🔍 房源精选")
        f_reg = st.multiselect("选择区域", options=df['region'].unique().tolist())
        f_rm = st.multiselect("选择房型", options=df['rooms'].unique().tolist())
        
        # 确保价格是数字
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        max_p = int(df['price'].max()) if not df.empty else 10000
        f_price = st.slider("最高月租 (£/pcm)", 0, max_p + 500, max_p)

    # 应用过滤
    filtered = df.copy()
    if f_reg: filtered = filtered[filtered['region'].isin(f_reg)]
    if f_rm: filtered = filtered[filtered['rooms'].isin(f_rm)]
    filtered = filtered[filtered['price'] <= f_price]

    # --- 6. 房源橱窗展示 (三列布局) ---
    st.markdown(f"#### 📍 发现 {len(filtered)} 套精品房源")
    
    cols = st.columns(3)
    for idx, (real_idx, row) in enumerate(filtered.iterrows()):
        with cols[idx % 3]:
            with st.container(border=True):
                # 图片展示 (带防崩溃保护)
                p_link = row['poster-link']
                if pd.isna(p_link) or str(p_link).strip() == "":
                    st.image("https://via.placeholder.com/400x500?text=Hao+Harbour", use_container_width=True)
                else:
                    st.image(p_link, use_container_width=True)
                
                st.markdown(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.markdown(f"#### :red[£{int(row['price']):,} /pcm]")
                
                # --- 详情弹窗 (支持 DeepSeek 内容) ---
                if st.button("查看详情 & 联系", key=f"btn_{idx}", use_container_width=True):
                    @st.dialog(f"{row['title']}")
                    def show_details(item):
                        st.image(item['poster-link'], use_container_width=True)
                        st.markdown("### 📋 房源亮点")
                        # 重点：显示 DeepSeek 生成的带钩描述
                        st.write(item['description'])
