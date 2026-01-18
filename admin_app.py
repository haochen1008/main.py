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

# Cloudinary 配置
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )
except:
    st.error("❌ Cloudinary 配置未找到，请检查 Streamlit Secrets")

# --- 2. 核心函数：生成房源海报 ---
def create_poster(files, title):
    try:
        poster = Image.new('RGB', (800, 1000), color='white')
        main_img = Image.open(files[0]).convert("RGB")
        main_img.thumbnail((800, 600))
        poster.paste(main_img, (0, 0))
        
        draw = ImageDraw.Draw(poster)
        try:
            font = ImageFont.truetype("simhei.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        draw.text((40, 650), "Hao Harbour 精选房源", fill="black", font=font)
        draw.text((40, 720), title[:20], fill="#D4AF37", font=font) # 使用金色
        return poster
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 3. 页面 UI ---
st.title("🏡 房源发布系统")

with st.form("upload_form"):
    title = st.text_input("房源标题 (例: Thames City)")
    region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
    rooms = st.text_input("房型 (例: 2B2B)")
    price = st.number_input("月租 (£/pcm)", min_value=0)
    
    # --- 找回你调试很久的 Description 字段 ---
    description = st.text_area("房源详细描述 (Description)", height=150, help="在这里输入房源的详细介绍、周边配套等信息")
    
    files = st.file_uploader("上传图片", accept_multiple_files=True)
    submit = st.form_submit_button("🚀 立即发布")

if submit:
    if not files or not title or not description:
        st.warning("标题、描述和图片都是必填项哦！")
    else:
        with st.spinner("正在上传并同步数据..."):
            poster_img = create_poster(files, title)
            
            if poster_img:
                # 图片转二进制
                img_byte_arr = io.BytesIO()
                poster_img.save(img_byte_arr, format='JPEG')
                
                # 上传 Cloudinary
                upload_result = cloudinary.uploader.upload(img_byte_arr.getvalue())
                poster_url = upload_result.get("secure_url")
                
                # 写入 Google Sheets (包含 description)
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    existing_df = conn.read(worksheet="Sheet1")
                    
                    new_row = {
                        "title": title,
                        "region": region,
                        "rooms": rooms,
                        "price": price,
                        "description": description, # 确保表格里有这一列
                        "poster_link": poster_url,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.success("✅ 房源已发布！Description 已同步到表格。")
                    st.image(poster_url)
                except Exception as e:
                    st.error(f"同步到表格失败: {e}")
