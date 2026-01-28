import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests, cloudinary
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 配置
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
    最稳健的连接方式：完全依赖 Secrets 自动加载。
    不传任何额外参数，防止 type, spreadsheet 等参数冲突
    """
    return st.connection("gsheets", type=GSheetsConnection)

def call_ai_logic(text):
    """提取房源要点"""
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取失败"

def create_poster(files, title_text):
    """简单生成预览海报"""
    try:
        canvas = Image.new('RGB', (800, 1000), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try: font = ImageFont.truetype("simhei.ttf", 45)
        except: font = ImageFont.load_default()
        if files:
            img = Image.open(files[0]).convert('RGB').resize((700, 500))
            canvas.paste(img, (50, 50))
        draw.text((50, 600), title_text, font=font, fill=(0, 0, 0))
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
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述", height=150)
        if st.button("✨ 执行 AI 提取"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            st.rerun()
    with col_b:
        n_desc = st.text_area("编辑 AI 结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传图片", accept_multiple_files=True)
        if st.button("📤 确认发布", type="primary"):
            try:
                with st.spinner("同步中..."):
                    # 图片处理
                    poster = create_poster(n_pics, n_title)
                    buf = io.BytesIO(); poster.save(buf, format='JPEG')
                    url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                    
                    # 表格连接
                    conn = get_conn()
                    df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                    new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": n_title, "region": n_reg, "price": n_price, "poster-link": url, "description": n_desc}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=df)
                    st.success("房源已成功发布！")
                    st.rerun()
            except Exception as e: st.error(f"发布失败: {e}")

with tab2:
    st.subheader("📊 房源看板")
    try:
        conn = get_conn()
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            sel_del = st.selectbox("选择要下架的房源", df['title'].tolist())
            if st.button("🗑️ 确认下架"):
                df = df[df['title'] != sel_del]
                conn.update(worksheet="Sheet1", data=df)
                st.rerun()
        else: st.info("暂无数据")
    except Exception as e:
        st.error(f"表格连接失败: {e}")
