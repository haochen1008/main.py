import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import os
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour 管理后台", layout="wide")

# Cloudinary 配置
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 辅助函数：生成海报 ---
def create_poster(images, title):
    # 这里保持你之前的海报生成逻辑不变
    # 假设你已经有了完整的 create_poster 函数代码
    # ... (此处省略具体绘图代码，请保留你现有的逻辑) ...
    pass 

# --- 3. 连接 Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. 主界面：发布新房源 ---
st.title("🚀 Hao Harbour 房源发布系统")

with st.expander("➕ 发布新房源", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("房源名称 (如: River Park Tower)")
        # 优化 1: 区域改为指定中文下拉
        region = st.selectbox("选择区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        # 优化 2: 房型改为指定下拉
        rooms = st.selectbox("选择房型", ["1房", "2房", "3房", "4房+"])
    
    with col2:
        price = st.number_input("月租 (£/pcm)", min_value=0, value=5000, step=100)
        desc = st.text_area("房源描述 (DeepSeek 提取的内容)", height=150)

    photos = st.file_uploader("上传房源照片 (第一张为主图)", accept_multiple_files=True)

    if st.button("📢 确认发布", type="primary"):
        if not title or not photos or not desc:
            st.error("请完整填写标题、描述并上传照片")
        else:
            with st.spinner("正在处理并同步中..."):
                # (这里调用你的海报生成和 Cloudinary 上传逻辑)
                # 假设上传后得到了 p_url
                p_url = "https://your-cloudinary-link.jpg" # 占位符
                
                # --- 核心修复：安全追加数据 ---
                existing_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_row = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": title,
                    "region": region,
                    "rooms": rooms,
                    "price": price,
                    "poster-link": p_url,
                    "description": desc
                }
                # 使用 concat 确保旧数据保留，新数据追加
                updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success(f"✅ 《{title}》 已发布成功！")
                st.rerun()

# --- 5. 新增功能：房源管理与删除 ---
st.divider()
st.subheader("📋 已发布房源管理")

# 读取最新列表
try:
    manage_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
    
    if manage_df.empty:
        st.info("目前还没有发布任何房源。")
    else:
        # 显示简易列表
        display_df = manage_df[['date', 'title', 'region', 'rooms', 'price']]
        
        # 使用 st.data_editor 或带勾选框的表格
        selected_rows = st.multiselect("选择要删除的房源标题", options=manage_df['title'].tolist())
        
        if st.button("🗑️ 删除选中房源", help="删除后不可恢复"):
            if selected_rows:
                # 过滤掉选中的行
                new_manage_df = manage_df[~manage_df['title'].isin(selected_rows)]
                conn.update(worksheet="Sheet1", data=new_manage_df)
                st.warning(f"已删除: {', '.join(selected_rows)}")
                st.rerun()
            else:
                st.info("请先在上方选择要删除的房源。")
        
        # 展示当前表格
        st.dataframe(display_df, use_container_width=True)

except Exception as e:
    st.error(f"加载房源列表失败: {e}")
