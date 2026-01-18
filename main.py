import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import io
import pandas as pd
from datetime import datetime

# --- 1. 初始化云端配置 ---
# 配置 Cloudinary (从 Secrets 读取)
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 新增：图片上传函数 ---
def upload_poster_to_cloud(image_bytes):
    # 将海报上传到云端图床
    upload_result = cloudinary.uploader.upload(image_bytes, folder="hao_harbour")
    return upload_result["secure_url"] # 返回永久图片链接

# --- 3. UI 界面：画廊模式 ---
st.title("🏡 Hao Harbour 房产展示平台")

tab_gen, tab_gallery = st.tabs(["✨ 生成新房源", "🖼️ 房源橱窗"])

with tab_gen:
    # ... (保留之前的海报生成代码逻辑) ...
    if st.button("🚀 生成并全自动同步"):
        # 1. 生成海报图片数据
        # poster_img = create_poster(...) 
        
        # 2. 上传到云端获取链接
        buf = io.BytesIO()
        poster_img.convert('RGB').save(buf, format='PNG')
        img_bytes = buf.getvalue()
        with st.spinner("正在同步海报至云端图库..."):
            cloud_url = upload_poster_to_cloud(img_bytes)
        
        # 3. 写入 Google Sheets (这次包含图片链接)
        new_row = pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "title": prop_title,
            "region": reg,
            "rooms": rm,
            "price": price_pcm,
            "poster_link": cloud_url # 真正的图片链接
        }])
        # ... (执行 conn.update) ...
        st.success("房源已全自动入库！")
        st.image(cloud_url, caption="云端已备份")

with tab_gallery:
    st.header("全伦敦房源橱窗")
    db = conn.read(worksheet="Sheet1", ttl=0)
    
    # 筛选器
    sel_reg = st.multiselect("筛选区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
    display_df = db if not sel_reg else db[db['region'].isin(sel_reg)]

    # --- 核心 UI 升级：卡片式布局 ---
    if not display_df.empty:
        cols = st.columns(3) # 每行显示3个房源
        for idx, row in display_df.iterrows():
            with cols[idx % 3]:
                # 制作一个精美的卡片
                st.container(border=True)
                st.image(row['poster_link'], use_container_width=True)
                st.subheader(row['title'])
                st.write(f"📍 {row['region']} | 🏠 {row['rooms']}")
                st.write(f"💰 **£{row['price']} /pcm**")
                # 快速分享按钮
                st.link_button("查看大图/下载", row['poster_link'])
