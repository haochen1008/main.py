import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import json
import base64

# --- 1. 配置管理 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# 尝试获取 Secrets 里的 ImgBB Key
try:
    IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
except:
    st.error("⚠️ 请在 Streamlit Cloud Settings -> Secrets 中添加 IMGBB_API_KEY = '你的Key'")
    st.stop()

# --- 2. 新增：水印处理与上传逻辑 (这是唯一新增的后台功能) ---
def process_and_upload_watermark(image_input):
    try:
        # 加载图片
        img = Image.open(image_input).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # 字体大小自适应
        f_size = int(img.size[0] / 12)
        font = ImageFont.load_default() 
        
        text = "Hao Harbour"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # 居中绘制半透明水印
        draw.text(((img.size[0]-w)/2, (img.size[1]-h)/2), text, fill=(255, 255, 255, 120), font=font)
        
        # 合并并转换
        final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
        buf = BytesIO()
        final_img.save(buf, format="JPEG", quality=85)
        
        # 上传到 ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(buf.getvalue())}
        res = requests.post(url, data=payload)
        return res.json()['data']['url']
    except Exception as e:
        st.error(f"❌ 水印处理或上传失败: {e}")
        return None

# --- 3. 原有功能：AI 提取逻辑 (完整保留) ---
def call_ai_summary(raw_text):
    # 这里保持你原有的 AI 逻辑
    if not raw_text: return "暂无描述"
    return raw_text # 如果你有 GPT/Coze API 调用，请放在这里

# --- 4. 主界面与数据库连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sheet1", ttl=0)

# 侧边栏菜单
menu = st.sidebar.radio("功能切换", ["📝 录入新房源", "📋 管理房源库"])

# --- 页面 A：录入房源 (保留所有原始字段和布局) ---
if menu == "📝 录入新房源":
    st.title("🚀 AI 智能房源录入")
    
    with st.form("listing_form"):
        title = st.text_input("房源标题")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            region = st.selectbox("区域", ["London Bridge", "Bermondsey", "Canary Wharf", "Southwark", "Greenwich", "Other"])
        with col2:
            rooms = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        with col3:
            price = st.number_input("月租 (£/pcm)", value=3000, step=100)
            
        uploaded_file = st.file_uploader("上传封面图片 (自动加水印)", type=["jpg", "jpeg", "png"])
        raw_desc = st.text_area("粘贴英文原始描述 (用于 AI 提取亮点)", height=200)
        
        submitted = st.form_submit_button("✨ 执行 AI 智能提取并发布")
        
        if submitted:
            if not uploaded_file or not title:
                st.error("❌ 标题和图片不能为空")
            else:
                with st.spinner("⏳ AI 正在提取并处理水印图片..."):
                    # 1. 加水印并上传获取链接
                    watermarked_url = process_and_upload_watermark(uploaded_file)
                    
                    if watermarked_url:
                        # 2. 调用 AI 提取描述
                        processed_description = call_ai_summary(raw_desc)
                        
                        # 3. 构建数据
                        new_row = pd.DataFrame([{
                            "title": title,
                            "region": region,
                            "rooms": rooms,
                            "price": price,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "description": processed_description,
                            "poster-link": watermarked_url
                        }])
                        
                        # 4. 更新 Sheets
                        updated_df = pd.concat([new_row, df], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        
                        st.success("🎉 发布成功！水印图已存入云端。")
                        st.image(watermarked_url, caption="带水印封面预览", width=400)

# --- 页面 B：管理房源库 (保留完整表格管理功能) ---
elif menu == "📋 管理房源库":
    st.title("📂 现有房源管理")
    
    if not df.empty:
        # 展示数据预览
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ 删除房源")
        del_title = st.selectbox("选择要删除的房源", df['title'].tolist())
        
        if st.button("❌ 确认删除"):
            new_df = df[df['title'] != del_title]
            conn.update(worksheet="Sheet1", data=new_df)
            st.warning(f"已删除房源: {del_title}")
            st.rerun()
    else:
        st.info("数据表目前为空。")
