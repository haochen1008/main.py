import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests
from datetime import datetime

# --- 1. 配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 配置
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )
except Exception as e:
    st.error(f"Cloudinary 配置缺失: {e}")

DEEPSEEK_KEY = st.secrets.get("OPENAI_API_KEY", "")

# --- 2. 工具函数 ---
def call_ai_logic(text):
    """AI 提取逻辑"""
    if not DEEPSEEK_KEY: return "AI Key 缺失"
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=10)
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取超时或失败"

def create_poster(files, title_text):
    """海报生成"""
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

# --- 3. 页面布局 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

with tab1:
    st.subheader("🚀 发布新房源")
    if "new_ai_desc" not in st.session_state:
        st.session_state.new_ai_desc = ""
        
    col_a, col_b = st.columns(2)
    with col_a:
        n_title = st.text_input("房源名称 (例如: River Park Tower)")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述", height=150)
        if st.button("✨ 执行 AI 提取", key="btn_new_ai"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            st.rerun()
            
    with col_b:
        n_desc = st.text_area("编辑 AI 提取结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传图片", accept_multiple_files=True)
        if st.button("📤 确认发布并生成海报", type="primary"):
            if not n_pics:
                st.warning("请上传房源图片")
            else:
                try:
                    with st.spinner("处理中..."):
                        poster = create_poster(n_pics, n_title)
                        buf = io.BytesIO()
                        poster.save(buf, format='JPEG')
                        url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                        
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"), 
                            "title": n_title, "region": n_reg, 
                            "rooms": n_room, "price": n_price, 
                            "poster-link": url, "description": n_desc,
                            "views": 0, "is_featured": False
                        }
                        # 核心修改：使用 concat 确保数据合并正确
                        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("发布成功！")
                        st.rerun()
                except Exception as e:
                    st.error(f"发布失败，请检查配置或表格: {str(e)}")

# --- 在管理逻辑 tab2 的最开始修改 ---
with tab2:
    st.subheader("📊 房源看板与快捷编辑")
    
    # 【核心修复代码】手动处理 key 中的换行符，防止 PEM 加载失败
    if "gsheets" in st.secrets["connections"]:
        raw_key = st.secrets["connections"]["gsheets"]["private_key"]
        # 确保 \n 被正确识别为换行符
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

    try:
        # --- 核心连接修复逻辑 ---
def get_gsheets_conn():
    # 从 Secrets 获取原始数据
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    # 强制修复换行符（关键步骤！）
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # 使用处理后的字典建立连接
    return st.connection("gsheets", type=GSheetsConnection, **creds_dict)

# --- 在你需要使用 conn 的地方调用 ---
try:
    conn = get_gsheets_conn()
    df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
    # ... 原有的 df 处理逻辑 ...
except Exception as e:
    st.error(f"连接出错: {e}")
