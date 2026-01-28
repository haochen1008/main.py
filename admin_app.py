import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests, cloudinary
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 认证
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )
except:
    st.error("Cloudinary 凭证有误，请检查 Secrets")

DEEPSEEK_KEY = st.secrets.get("OPENAI_API_KEY", "")

# --- 2. 核心工具函数 ---

def call_ai_logic(text):
    """提取房源要点"""
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"请将以下英文房源描述翻译成中文并提取要点（✔开头）：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败: {e}"

def create_poster(files, title_text):
    """简单生成预览图"""
    try:
        canvas = Image.new('RGB', (800, 1000), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        # 尝试加载字体，失败则使用默认
        try: font = ImageFont.truetype("simhei.ttf", 40)
        except: font = ImageFont.load_default()
        
        if files:
            img = Image.open(files[0]).convert('RGB').resize((700, 500))
            canvas.paste(img, (50, 50))
        
        draw.text((50, 600), title_text, font=font, fill=(0,0,0))
        return canvas
    except: return None

# --- 3. UI 界面 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

with tab1:
    st.subheader("🚀 发布新房源")
    n_title = st.text_input("房源名称")
    n_raw = st.text_area("英文原始描述")
    n_pics = st.file_uploader("上传图片", accept_multiple_files=True)
    
    if st.button("📤 确认发布"):
        try:
            with st.spinner("正在处理并同步..."):
                # 1. 处理图片海报
                poster = create_poster(n_pics, n_title)
                buf = io.BytesIO()
                poster.save(buf, format='JPEG')
                upload_res = cloudinary.uploader.upload(buf.getvalue())
                url = upload_res['secure_url']
                
                # 2. 连接 GSheets
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                
                # 3. 插入新行
                new_row = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": n_title,
                    "poster-link": url,
                    "description": call_ai_logic(n_raw)
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=df)
                st.success("发布成功！")
        except Exception as e:
            st.error(f"发布失败: {e}")

with tab2:
    st.subheader("📊 房源看板")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"连接 Google Sheets 失败: {e}")
