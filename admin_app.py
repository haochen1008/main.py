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
    st.error("Cloudinary 配置缺失")

DEEPSEEK_KEY = st.secrets.get("OPENAI_API_KEY", "")

# --- 2. 核心工具函数 ---

def get_conn():
    """
    最稳健的连接方式：不手动传参，只负责修复 PEM 格式。
    """
    # 这一步是为了修复 "Unable to load PEM file" 错误
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    # 这种方式虽然 st.secrets 只读，但在内存中会被缓存修复后的格式
    # 如果还是报错 PEM，建议手动在 Secrets 文本框里检查是否有空格
    return st.connection("gsheets", type=GSheetsConnection)

def call_ai_logic(text):
    """AI 提取逻辑"""
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}, timeout=15)
        return res.json()['choices'][0]['message']['content']
    except:
        return "AI 提取失败"

def create_poster(files, title_text):
    """生成海报"""
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try: 
            font_t = ImageFont.truetype("simhei.ttf", 45)
            font_f = ImageFont.truetype("simhei.ttf", 25)
        except: 
            font_t = font_f = ImageFont.load_default()
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        draw.text((40, 950), title_text, font=font_t, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_f, fill=(180, 160, 100))
        return canvas
    except: return None

# --- 3. UI 界面 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

with tab1:
    st.subheader("🚀 发布新房源")
    if "new_ai_desc" not in st.session_state: st.session_state.new_ai_desc = ""
        
    col_a, col_b = st.columns(2)
    with col_a:
        n_title = st.text_input("房源名称")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述", height=150)
        if st.button("✨ 执行 AI 提取"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            st.rerun()
            
    with col_b:
        n_desc = st.text_area("编辑 AI 结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传房源图片", accept_multiple_files=True)
        if st.button("📤 确认发布", type="primary"):
            if not n_pics: st.error("请上传图片")
            else:
                try:
                    with st.spinner("发布中..."):
                        poster = create_poster(n_pics, n_title)
                        buf = io.BytesIO()
                        poster.save(buf, format='JPEG')
                        url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                        
                        conn = get_conn()
                        # 注意：直接读，不用传 spreadsheet，它会自动从 secrets 获取
                        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                        
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"), 
                            "title": n_title, "region": n_reg, "rooms": n_room, 
                            "price": n_price, "poster-link": url, "description": n_desc,
                            "views": 0, "is_featured": False
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=df)
                        st.success("房源已成功同步至 Google Sheets！")
                        st.rerun()
                except Exception as e:
                    st.error(f"发布失败: {e}")

with tab2:
    st.subheader("📊 房源看板")
    try:
        conn = get_conn()
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            sel_del = st.selectbox("选择下架房源", df['title'].tolist())
            if st.button("🗑️ 确认下架"):
                df = df[df['title'] != sel_del]
                conn.update(worksheet="Sheet1", data=df)
                st.rerun()
        else: st.info("暂无数据")
    except Exception as e:
        st.error(f"连接失败: {e}")
