import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import io
import pandas as pd
from datetime import datetime
import requests

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour 管理后台", layout="wide")

# --- 2. 初始化服务 ---
def init_services():
    try:
        cloudinary.config(
            cloud_name = st.secrets.get("CLOUDINARY_CLOUD_NAME"),
            api_key = st.secrets.get("CLOUDINARY_API_KEY"),
            api_secret = st.secrets.get("CLOUDINARY_API_SECRET")
        )
        return True
    except:
        st.error("❌ Cloudinary 配置缺失")
        return False

# --- 3. DeepSeek AI 提取逻辑 (已更新地址) ---
def call_ai_summary(raw_text):
    api_key = st.secrets.get("OPENAI_API_KEY") # 这里的名字可以不改，但里面填 DeepSeek 的 key
    if not api_key:
        return "❌ 请在 Secrets 中填入 DeepSeek 的 API Key"
    
    try:
        # 核心修改：使用 DeepSeek 的官方接口地址
        api_url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat", # DeepSeek 的通用模型名称
            "messages": [
                {"role": "system", "content": "你是一个房产文案专家，负责将英文描述提取为中文要点，每行以 ✔ 开头。"},
                {"role": "user", "content": f"请提取以下描述：\n\n{raw_text}"}
            ],
            "stream": False
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['choices'][0]['message']['content']
        else:
            error_info = res_json.get("error", {}).get("message", "未知错误")
            return f"❌ DeepSeek 报错: {error_info}"
    except Exception as e:
        return f"❌ 连接 DeepSeek 失败: {str(e)}"

# --- 4. 海报生成函数 ---
def create_poster(files, title_text):
    try:
        poster = Image.new('RGB', (800, 1100), color='white')
        if files:
            img_w, img_h = 398, 398
            for i, file in enumerate(files[:4]):
                img = Image.open(file).convert("RGB")
                img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
                poster.paste(img, ((i % 2) * 402, (i // 2) * 402))
        
        draw = ImageDraw.Draw(poster)
        try:
            # 这里的字体文件名需与 GitHub 中完全一致 (simhei.ttf)
            f_title = ImageFont.truetype("simhei.ttf", 45)
            f_brand = ImageFont.truetype("simhei.ttf", 30)
        except:
            f_title = f_brand = ImageFont.load_default()

        draw.text((30, 850), "Hao Harbour | London Excellence", fill="#D4AF37", font=f_brand)
        draw.text((30, 910), title_text[:20], fill="black", font=f_title)
        return poster
    except Exception as e:
        st.error(f"🎨 海报生成失败: {e}")
        return None

# --- 5. 主程序 ---
if init_services():
    st.title("🏡 Hao Harbour 房源智能发布 (DeepSeek 版)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 信息录入")
        title = st.text_input("房源标题")
        region = st.selectbox("区域", ["City of London", "Canary Wharf", "South Kensington", "Nine Elms", "Other"])
        rooms = st.text_input("房型")
        price = st.number_input("月租 (£/pcm)", min_value=0)
        en_desc = st.text_area("粘贴英文描述", height=150)
        if st.button("✨ 执行 AI 智能提取"):
            if en_desc:
                with st.spinner("DeepSeek 正在思考..."):
                    st.session_state.temp_desc = call_ai_summary(en_desc)
            else:
                st.warning("请先粘贴描述内容")

    with col2:
        st.subheader("2. 预览与发布")
        final_desc = st.text_area("最终 Description (可微调)", 
                                 value=st.session_state.get('temp_desc', ""), 
                                 height=320)
        photos = st.file_uploader("上传照片 (前4张)", accept_multiple_files=True)

    if st.button("📢 确认发布"):
        if not photos or not title or not final_desc:
            st.error("❌ 信息不全，请检查标题、照片和描述")
        else:
            with st.spinner("海报同步中..."):
                p_obj = create_poster(photos, title)
                if p_obj:
                    # 图片转字节流
                    buf = io.BytesIO()
                    p_obj.save(buf, format='JPEG')
                    # 上传 Cloudinary
                    u_res = cloudinary.uploader.upload(buf.getvalue())
                    p_url = u_res.get("secure_url")
                    
                    # 写入 Google Sheets
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
                        st.success("✅ 房源已成功发布！")
                        st.image(p_url, caption="生成海报预览")
                    except Exception as e:
                        st.error(f"表格同步失败: {e}")
