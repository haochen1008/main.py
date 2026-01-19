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

try:
    IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
except:
    st.error("⚠️ 请在 Secrets 中配置 IMGBB_API_KEY")
    st.stop()

# --- 2. 核心功能函数 (水印与上传) ---

def process_and_upload(image_input):
    """自动给上传的图片加水印并传到 ImgBB"""
    try:
        img = Image.open(image_input).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # 字体大小自适应
        f_size = int(img.size[0] / 12)
        font = ImageFont.load_default() 
        
        text = "Hao Harbour"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # 居中半透明水印
        draw.text(((img.size[0]-w)/2, (img.size[1]-h)/2), text, fill=(255, 255, 255, 120), font=font)
        
        final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
        buf = BytesIO()
        final_img.save(buf, format="JPEG", quality=85)
        
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(buf.getvalue())}
        res = requests.post(url, data=payload)
        return res.json()['data']['url']
    except Exception as e:
        st.error(f"❌ 图片处理失败: {e}")
        return None

def call_ai_summary(raw_text):
    """AI 提取摘要逻辑 (可在此接入 GPT/Coze API)"""
    if not raw_text: return "暂无描述"
    return raw_text[:300] + "..." if len(raw_text) > 300 else raw_text

# --- 3. 连接数据库 ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Sheet1", ttl=0)

# --- 4. 侧边栏导航 ---
st.sidebar.title("🛠️ 后台管理面板")
menu = st.sidebar.radio("功能切换", ["📝 录入新房源", "📋 管理/删除房源"])

# --- 5. 页面逻辑 A：录入新房源 ---
if menu == "📝 录入新房源":
    st.title("🏡 发布新房源")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("房源标题")
            region = st.selectbox("区域", ["London Bridge", "Bermondsey", "Canary Wharf", "Southwark", "Other"])
        with col2:
            price = st.number_input("月租 (£/pcm)", value=3000, step=100)
            rooms = st.text_input("房型", placeholder="2 Beds, 1 Bath")
        
        uploaded_file = st.file_uploader("上传封面图 (将自动添加水印)", type=["jpg", "png", "jpeg"])
        raw_desc = st.text_area("房源描述内容 (AI 提取)")
        
        submit = st.form_submit_button("🚀 智能处理并发布")

        if submit:
            if not uploaded_file or not title:
                st.warning("⚠️ 标题和图片是必填项")
            else:
                with st.spinner("⏳ 正在加水印、上传并同步数据..."):
                    final_url = process_and_upload(uploaded_file)
                    if final_url:
                        processed_desc = call_ai_summary(raw_desc)
                        new_row = pd.DataFrame([{
                            "title": title, "region": region, "rooms": rooms, 
                            "price": price, "date": datetime.now().strftime("%Y-%m-%d"),
                            "description": processed_desc, "poster-link": final_url
                        }])
                        updated_df = pd.concat([new_row, df], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("🎉 发布成功！")
                        st.image(final_url, caption="带水印预览", width=300)

# --- 6. 页面逻辑 B：管理/
