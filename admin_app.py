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

# --- 2. 初始化云端服务 ---
def init_services():
    try:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"]
        )
        return True
    except Exception as e:
        st.error(f"❌ Cloudinary 配置错误: {e}")
        return False

# --- 3. AI 智能提取函数 (修复了 'choices' 报错逻辑) ---
def call_ai_summary(raw_text):
    if "OPENAI_API_KEY" not in st.secrets:
        return "⚠️ 请在 Secrets 中检查 OPENAI_API_KEY 配置"
    
    try:
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        }
        # 优化 Prompt，确保返回你想要的打钩格式
        prompt = f"请根据以下房源英文描述，提取中文核心要点。要求每行以 ✔ 开头，包含标题、租金、房型、交通、大楼设施等：\n\n{raw_text}"
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # 增加安全解析逻辑
        if "choices" in res_json:
            return res_json['choices'][0]['message']['content']
        else:
            # 如果没有 choices 键，打印出 API 返回的错误详情
            error_msg = res_json.get("error", {}).get("message", "未知错误")
            return f"❌ AI 接口返回错误: {error_msg}"
            
    except Exception as e:
        return f"❌ 网络连接失败: {str(e)}"

# --- 4. 稳健的海报生成函数 (修复 NameError) ---
def create_poster(files, title_text):
    try:
        # 创建一个 800x1100 的纯白画布
        poster = Image.new('RGB', (800, 1100), color='white')
        
        # 拼图逻辑：前4张图拼成田字格
        if files:
            img_w, img_h = 398, 398
            for i, file in enumerate(files[:4]):
                img = Image.open(file).convert("RGB")
                # 调整并裁剪图片
                img = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
                x = (i % 2) * 402
                y = (i // 2) * 402
                poster.paste(img, (x, y))
        
        draw = ImageDraw.Draw(poster)
        
        # 尝试加载字体，失败则使用系统默认
        try:
            # 请确保 github 根目录有 simhei.ttf
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_sub = ImageFont.truetype("simhei.ttf", 30)
        except:
            font_title = font_sub = ImageFont.load_default()

        # 底部文字修饰
        draw.text((30, 850), "Hao Harbour | 伦敦精品房源", fill="#D4AF37", font=font_sub)
        draw.text((30, 910), title_text[:20], fill="black", font=font_title)
        draw.text((600, 1050), "Exclusive Living", fill="#cccccc", font=font_sub)
        
        return poster
    except Exception as e:
        st.error(f"🎨 海报生成失败: {e}")
        return None

# --- 5. 主页面 ---
if init_services():
    st.title("🚀 Hao Harbour 智能发布系统")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 录入房源信息")
        in_title = st.text_input("房源标题")
        in_region = st.selectbox("区域", ["City of London", "Canary Wharf", "South Kensington", "Nine Elms", "Other"])
        in_rooms = st.text_input("房型 (例: 2B2B)")
        in_price = st.number_input("月租 (£/pcm)", min_value=0)
        
        raw_en = st.text_area("粘贴英文描述 (用于 AI 提取)", height=200)
        if st.button("✨ 执行智能提取"):
            if raw_en:
                with st.spinner("AI 正在分析并翻译..."):
                    result = call_ai_summary(raw_en)
                    st.session_state.processed_desc = result
            else:
                st.warning("请先粘贴内容")

    with col2:
        st.subheader("2. 预览与发布")
        final_desc = st.text_area("最终 Description (可微调)", 
                                 value=st.session_state.get('processed_desc', ""), 
                                 height=320)
        in_files = st.file_uploader("上传图片 (前4张组成海报)", accept_multiple_files=True)

    if st.button("📢 确认发布至云端"):
        if not in_files or not in_title or not final_desc:
            st.error("请填完所有必填项 (标题、描述、照片)")
        else:
            with st.spinner("正在上传图片并同步表格..."):
                # A. 生成海报
                poster_obj = create_poster(in_files, in_title)
                
                if poster_obj:
                    # B. 上传海报
                    buf = io.BytesIO()
                    poster_obj.save(buf, format='JPEG')
                    up_res = cloudinary.uploader.upload(buf.getvalue())
                    p_url = up_res.get("secure_url")
                    
                    # C. 写入 Google Sheets (严格按照你的列顺序)
                    # date title region rooms price poster-link description
                    try:
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df = conn.read(worksheet="Sheet1")
                        
                        new_data = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "title": in_title,
                            "region": in_region,
                            "rooms": in_rooms,
                            "price": in_price,
                            "poster-link": p_url,
                            "description": final_desc
                        }
                        
                        updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        
                        st.success("✅ 房源已成功发布！")
                        st.image(p_url, caption="在线海报预览")
                    except Exception as e:
                        st.error(f"表格同步失败: {e}")
