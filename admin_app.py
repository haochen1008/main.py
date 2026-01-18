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
st.set_page_config(page_title="Hao Harbour 后台管理", layout="wide")

# --- 2. 检查并配置云端服务 ---
def init_services():
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

# --- 3. AI 智能提取函数 ---
def call_ai_summary(raw_text):
    if "OPENAI_API_KEY" not in st.secrets:
        return "⚠️ 请先在 Streamlit 后台 Settings -> Secrets 中配置 OPENAI_API_KEY"
    
    try:
        # 这里建议使用更稳定的 api 地址，如果你有转发地址请更换
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        prompt = f"请将以下房源描述提取为中文要点，每行以 ✔ 开头，包含标题、租金、房型面积、交通设施等：\n\n{raw_text}"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败，请检查网络或 Key。错误: {str(e)}"

# --- 4. 稳健的海报生成函数 ---
def create_poster(files, title_text):
    try:
        # 创建画布
        poster = Image.new('RGB', (800, 1100), color='white')
        
        # 拼图：尝试拼接前4张图
        img_w, img_h = 398, 398
        for i, file in enumerate(files[:4]):
            img = Image.open(file).convert("RGB")
            # 缩放并居中裁剪
            img.thumbnail((800, 800)) 
            x = (i % 2) * 402
            y = (i // 2) * 402
            poster.paste(img.resize((img_w, img_h)), (x, y))
        
        draw = ImageDraw.Draw(poster)
        # 加载字体
        try:
            # 确保你的 GitHub 仓库根目录有这个字体文件
            font_main = ImageFont.truetype("simhei.ttf", 45)
            font_sub = ImageFont.truetype("simhei.ttf", 30)
        except:
            font_main = font_sub = ImageFont.load_default()

        # 绘制文字区域
        draw.text((30, 850), "Hao Harbour | 伦敦精品房源", fill="#D4AF37", font=font_sub)
        draw.text((30, 910), title_text[:20], fill="black", font=font_main)
        
        # 模拟水印
        draw.text((600, 1050), "Hao Harbour", fill="#eeeeee", font=font_sub)
        
        return poster
    except Exception as e:
        st.error(f"海报渲染错误: {e}")
        return None

# --- 5. 主页面逻辑 ---
if init_services():
    st.title("🚀 Hao Harbour 房源发布系统")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 录入信息")
        in_title = st.text_input("房源名称")
        in_region = st.selectbox("区域", ["City of London", "Canary Wharf", "South Kensington", "Nine Elms", "Other"])
        in_rooms = st.text_input("房型 (如 2B2B)")
        in_price = st.number_input("月租 (£/pcm)", min_value=0)
        
        raw_en_text = st.text_area("粘贴英文描述 (用于 AI 提取)", height=200)
        if st.button("✨ 智能提取描述"):
            if raw_en_text:
                with st.spinner("AI 正在分析..."):
                    st.session_state.processed_desc = call_ai_summary(raw_en_text)
            else:
                st.warning("请先粘贴内容")

    with col2:
        st.subheader("2. 预览与上传")
        # 这里的 desc 允许手动修改
        final_desc = st.text_area("最终 Description (中文要点)", 
                                 value=st.session_state.get('processed_desc', ""), 
                                 height=300)
        
        in_files = st.file_uploader("上传房源照片 (前4张将组成海报)", accept_multiple_files=True)

    if st.button("📢 确认无误，正式发布"):
        if not in_files or not in_title or not final_desc:
            st.error("请确保标题、照片和 Description 都已填写")
        else:
            with st.spinner("正在上传图片并同步表格..."):
                # A. 生成并上传海报
                poster_obj = create_poster(in_files, in_title)
                if poster_obj:
                    buf = io.BytesIO()
                    poster_obj.save(buf, format='JPEG')
                    up_res = cloudinary.uploader.upload(buf.getvalue())
                    p_url = up_res.get("secure_url")
                    
                    # B. 写入 Google Sheets (严格顺序)
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df = conn.read(worksheet="Sheet1")
                        
                        # 严格按照你的要求顺序：date title region rooms price poster-link description
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "title": in_title,
                            "region": in_region,
                            "rooms": in_rooms,
                            "price": in_price,
                            "poster-link": p_url,
                            "description": final_desc
                        }
                        
                        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=new_df)
                        
                        st.success("✅ 发布成功！房源已进入客户库。")
                        st.image(p_url, caption="生成的海报预览")
                    except Exception as e:
                        st.error(f"表格同步失败: {e}")
