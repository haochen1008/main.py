import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import io
import pandas as pd
from datetime import datetime

# --- 1. 初始化配置 ---
st.set_page_config(page_title="Hao Harbour 后台管理", layout="centered")

# Cloudinary 配置 (从 Secrets 读取)
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )
except:
    st.error("❌ Cloudinary 配置缺失，请检查 Streamlit Secrets")

# --- 2. 核心函数：生成房源海报 ---
def create_poster(files, title):
    try:
        # 创建一个纯白背景的海报 (800x1000)
        poster = Image.new('RGB', (800, 1000), color='white')
        
        # 取得第一张图片作为主图并缩放
        main_img = Image.open(files[0])
        main_img = main_img.convert("RGB")
        # 保持比例缩放
        main_img.thumbnail((800, 600))
        poster.paste(main_img, (0, 0))
        
        # 简单的文字装饰
        draw = ImageDraw.Draw(poster)
        # 如果没有字体文件，使用默认字体
        try:
            font = ImageFont.truetype("simhei.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        draw.text((40, 650), f"Hao Harbour 精选", fill="black", font=font)
        draw.text((40, 720), title, fill="gold", font=font)
        
        return poster
    except Exception as e:
        st.error(f"海报生成失败原因: {e}")
        return None

# --- 3. 页面 UI ---
st.title("🏡 房源发布系统")

with st.form("upload_form"):
    title = st.text_input("房源标题 (例: Thames City)")
    region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
    rooms = st.text_input("房型 (例: 1B1B)")
    price = st.number_input("月租 (£/pcm)", min_value=0)
    files = st.file_uploader("上传房源照片 (第一张将作为主图)", accept_multiple_files=True)
    
    submit = st.form_submit_button("🚀 生成并发布房源")

if submit:
    if not files or not title:
        st.warning("请填写标题并上传图片")
    else:
        with st.spinner("正在处理房源并上传云端..."):
            # 1. 生成海报
            poster_img = create_poster(files, title)
            
            if poster_img:
                # 2. 将海报转为二进制流用于上传
                img_byte_arr = io.BytesIO()
                poster_img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # 3. 上传到 Cloudinary
                upload_result = cloudinary.uploader.upload(img_byte_arr)
                poster_url = upload_result.get("secure_url")
                
                # 4. 写入 Google Sheets
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    # 先读取旧数据
                    existing_df = conn.read(worksheet="Sheet1")
                    new_data = pd.DataFrame([{
                        "title": title,
                        "region": region,
                        "rooms": rooms,
                        "price": price,
                        "poster_link": poster_url,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }])
                    updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.success("✅ 房源发布成功！")
                    st.image(poster_url, caption="已生成的线上海报")
                except Exception as e:
                    st.error(f"表格写入失败: {e}")
