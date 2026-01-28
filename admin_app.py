import streamlit as st
import pandas as pd
import io, requests, json, cloudinary
import cloudinary.uploader
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
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
except Exception:
    st.error("Cloudinary 配置缺失")

# --- 2. 核心连接函数 ---
def get_gs_conn():
    """
    终极修复方案：
    1. 从单行 JSON 字符串解析凭证
    2. 解决所有 PEM 格式和参数冲突问题
    """
    try:
        # 从 Secrets 读取原始 JSON 字符串
        creds_info = json.loads(st.secrets["GSHEETS_JSON"])
        
        # 建立连接，不依赖 Streamlit 自动寻找 secrets
        conn = st.connection(
            "gsheets",
            type=GSheetsConnection,
            **creds_info
        )
        return conn
    except Exception as e:
        st.error(f"凭证解析失败，请检查 Secrets 格式: {e}")
        return None

def call_ai_logic(text):
    """AI 提取逻辑"""
    try:
        headers = {"Authorization": f"Bearer {st.secrets.get('OPENAI_API_KEY', '')}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}, timeout=15)
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取失败"

def create_poster(files, title_text):
    """海报生成"""
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try: font_t = ImageFont.truetype("simhei.ttf", 45)
        except: font_t = ImageFont.load_default()
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        draw.text((40, 950), title_text, font=font_t, fill=(0, 0, 0))
        return canvas
    except: return None

# --- 3. UI 逻辑 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

with tab1:
    st.subheader("🚀 发布新房源")
    if "new_ai_desc" not in st.session_state: st.session_state.new_ai_desc = ""
    col_a, col_b = st.columns(2)
    with col_a:
        n_title = st.text_input("房源名称")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        n_price = st.number_input("月租", value=3000)
        n_raw = st.text_area("粘贴英文原稿", height=150)
        if st.button("✨ AI 提取"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            st.rerun()
    with col_b:
        n_desc = st.text_area("AI 结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传图片", accept_multiple_files=True)
        if st.button("📤 确认发布", type="primary"):
            try:
                with st.spinner("同步中..."):
                    poster = create_poster(n_pics, n_title)
                    buf = io.BytesIO(); poster.save(buf, format='JPEG')
                    url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                    
                    conn = get_gs_conn()
                    df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1", ttl=0)
                    new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": n_title, "region": n_reg, "price": n_price, "poster-link": url, "description": n_desc}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1", data=df)
                    st.success("发布成功！")
            except Exception as e: st.error(f"发布错误: {e}")

with tab2:
    st.subheader("📊 房源看板")
    try:
        conn = get_gs_conn()
        if conn:
            df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1", ttl=0)
            st.dataframe(df, use_container_width=True)
    except Exception as e: st.error(f"加载失败: {e}")
