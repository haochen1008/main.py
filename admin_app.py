import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import io
import pandas as pd
from datetime import datetime
import requests

# --- 页面配置 ---
st.set_page_config(page_title="Hao Harbour 管理后台", layout="wide")

# --- 初始化 Cloudinary ---
def init_cloudinary():
    try:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"]
        )
        return True
    except:
        st.error("❌ Cloudinary Secrets 配置缺失")
        return False

# --- DeepSeek AI 提取逻辑 ---
def call_ai_summary(raw_text):
    api_key = st.secrets.get("OPENAI_API_KEY") # Secrets 里的 key 名字不用改，直接填 DeepSeek 的 key
    if not api_key:
        return "❌ 请在 Secrets 中填入 DeepSeek 的 API Key"
    
    try:
        # 关键修改：更换为 DeepSeek 官方接口地址
        api_url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个伦敦房产专家。请将输入的英文描述总结为中文要点，每行以 ✔ 开头，包含标题、租金、房型、交通、设施。"},
                {"role": "user", "content": raw_text}
            ]
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['choices'][0]['message']['content']
        else:
            return f"❌ DeepSeek 报错: {res_json.get('error', {}).get('message', '未知错误')}"
    except Exception as e:
        return f"❌ 连接失败: {str(e)}"

# --- 海报生成逻辑 ---
def create_poster(files, title_text):
    try:
        poster = Image.new('RGB', (800, 1100), color='white')
        if files:
            for i, file in enumerate(files[:4]):
                img = Image.open(file).convert("RGB")
                img = img.resize((398, 398), Image.Resampling.LANCZOS)
                poster.paste(img, ((i % 2) * 402, (i // 2) * 402))
        
        draw = ImageDraw.Draw(poster)
        try:
            # 确保 github 仓库根目录有 simhei.ttf 字体文件
            font_t = ImageFont.truetype("simhei.ttf", 45)
            font_s = ImageFont.truetype("simhei.ttf", 30)
        except:
            font_t = font_s = ImageFont.load_default()

        draw.text((30, 850), "Hao Harbour | London Excellence", fill="#D4AF37", font=font_s)
        draw.text((30, 910), title_text[:20], fill="black", font=font_t)
        return poster
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 主程序 ---
if init_cloudinary():
    st.title("🏡 Hao Harbour 房源智能发布 (DeepSeek)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 信息录入")
        title = st.text_input("房源标题")
        region = st.selectbox("区域", ["City of London", "Canary Wharf", "South Kensington", "Nine Elms", "Other"])
        rooms = st.text_input("房型")
        price = st.number_input("月租 (£/pcm)", min_value=0)
        en_desc = st.text_area("粘贴英文描述", height=150)
        if st.button("✨ AI 提取描述"):
            with st.spinner("DeepSeek 正在翻译并提取..."):
                st.session_state.temp_desc = call_ai_summary(en_desc)

    with col2:
        st.subheader("2. 预览与发布")
        final_desc = st.text_area("最终 Description (可微调)", 
                                 value=st.session_state.get('temp_desc', ""), 
                                 height=280)
        photos = st.file_uploader("上传照片 (前4张)", accept_multiple_files=True)

    if st.button("📢 确认发布"):
        if not photos or not title or not final_desc:
            st.error("信息不全！")
        else:
            with st.spinner("上传中..."):
                p_obj = create_poster(photos, title)
                if p_obj:
                    buf = io.BytesIO()
                    p_obj.save(buf, format='JPEG')
                    u_res = cloudinary.uploader.upload(buf.getvalue())
                    p_url = u_res.get("secure_url")
                    
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df = conn.read(worksheet="Sheet1")
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "title": title,
                            "region": region,
                            "rooms": rooms,
                            "price": price,
                            "poster-link": p_url,
                            "description": final_desc
                        }
                        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("✅ 发布成功！")
                        st.image(p_url)
                    except Exception as e:
                        st.error(f"表格同步失败: {e}")
