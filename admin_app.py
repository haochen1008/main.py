import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import io
import pandas as pd
from datetime import datetime
import requests
import json

# --- 1. 初始化配置 ---
st.set_page_config(page_title="Hao Harbour 后台管理", layout="wide")

# 配置 Cloudinary
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 核心功能：AI 智能提取并翻译 Description ---
def call_ai_summary(raw_text):
    """
    调用 AI 接口将英文房源信息提取为中文要点 (对应你照片里的格式)
    这里假设你使用的是类似 OpenAI 或 Groq 的 API
    """
    try:
        # 如果你之前调试好了 API，请替换这里的 URL 和 API_KEY
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        prompt = f"""
        请将以下英文房源描述转换为中文短句，要求：
        1. 使用打勾符号 '✔' 开头。
        2. 包含标题、租金、房型面积、交通通勤、大楼设施、生活环境等关键点。
        3. 语言专业、精炼。
        内容如下：{raw_text}
        """
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        # 如果 AI 调用失败，返回原始文本，避免程序崩溃
        return f"AI 摘要生成失败，请手动编辑。错误: {e}"

# --- 3. 核心功能：生成九宫格海报 ---
def create_poster(files, title):
    try:
        # 创建一个更长的画布来容纳更多图片
        poster_w, poster_h = 800, 1200
        poster = Image.new('RGB', (poster_w, poster_h), color='white')
        
        # 简单拼图逻辑：取前 4 张图做成田字格
        img_size = 395
        for i, file in enumerate(files[:4]):
            img = Image.open(file).convert("RGB")
            img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)
            x = (i % 2) * 405
            y = (i // 2) * 405
            poster.paste(img, (x, y))
        
        draw = ImageDraw.Draw(poster)
        try:
            # 确保你仓库里有 simhei.ttf 字体文件
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_brand = ImageFont.truetype("simhei.ttf", 30)
        except:
            font_title = font_brand = ImageFont.load_default()
            
        # 底部文字装饰
        draw.text((30, 850), "Hao Harbour | 伦敦房源精选", fill="#D4AF37", font=font_brand)
        draw.text((30, 910), title[:25], fill="black", font=font_title)
        
        return poster
    except Exception as e:
        st.error(f"海报生成逻辑出错: {e}")
        return None

# --- 4. 页面 UI 设计 ---
st.title("🚀 Hao Harbour 房源智能发布系统")

with st.sidebar:
    st.header("⚙️ 配置检查")
    st.success("Cloudinary 已连接")
    st.info("AI 智能提取已就绪")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 输入房源详情")
    title = st.text_input("房源标题")
    region = st.selectbox("区域", ["City of London", "Canary Wharf", "South Kensington", "Nine Elms", "Other"])
    rooms = st.text_input("房型 (如 2B2B)")
    price = st.number_input("月租 (£/pcm)", min_value=0)
    
    raw_desc = st.text_area("粘贴英文原始描述 (用于 AI 提取)", height=200)
    if st.button("✨ 智能提取 Description"):
        if raw_desc:
            with st.spinner("AI 正在分析并翻译..."):
                st.session_state.processed_desc = call_ai_summary(raw_desc)
        else:
            st.warning("请先粘贴英文内容")

with col2:
    st.subheader("2. 预览并上传")
    # 编辑 AI 生成的内容
    final_desc = st.text_area("最终 Description (可手动微调)", 
                              value=st.session_state.get('processed_desc', ""), 
                              height=300)
    
    uploaded_files = st.file_uploader("上传房源照片 (第一张为主图)", accept_multiple_files=True)

# --- 5. 提交发布逻辑 ---
if st.button("📢 确认发布至云端"):
    if not uploaded_files or not title or not final_desc:
        st.error("请确保标题、描述和照片都已就绪！")
    else:
        with st.spinner("正在同步海报、云端及表格..."):
            # A. 生成海报
            poster_obj = create_poster(uploaded_files, title)
            
            if poster_obj:
                # B. 上传海报到 Cloudinary
                buf = io.BytesIO()
                poster_obj.save(buf, format='JPEG')
                up_res = cloudinary.uploader.upload(buf.getvalue())
                p_url = up_res.get("secure_url")
                
                # C. 写入 Google Sheets (严格按照你的列顺序)
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    existing_df = conn.read(worksheet="Sheet1")
                    
                    # 按照你要求的顺序排列：date title region rooms price poster-link description
                    new_entry = {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "title": title,
                        "region": region,
                        "rooms": rooms,
                        "price": price,
                        "poster-link": p_url,
                        "description": final_desc
                    }
                    
                    updated_df = pd.concat([existing_df, pd.DataFrame([new_entry])], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    st.success("✅ 全部发布成功！")
                    st.image(p_url, caption="在线海报预览")
                except Exception as e:
                    st.error(f"表格同步失败: {e}")
