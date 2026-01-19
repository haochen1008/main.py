import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# 配置云端服务
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] 

# --- 核心：海报合成发动机 (找回丢失的合成逻辑) ---
def create_poster(files, title_text):
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try:
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
            font_wm = ImageFont.truetype("simhei.ttf", 80)
        except:
            font_title = font_footer = font_wm = ImageFont.load_default()

        # 6 宫格拼接
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))

        # 水印
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(wm_layer).text((180, 450), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        # 底部信息
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        return canvas
    except Exception as e:
        st.error(f"海报合成失败: {e}"); return None

# --- AI 提取函数 ---
def call_ai_summary(text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，✔开头，禁止押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]})
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取失败，请手动输入"

# --- 界面逻辑 ---
if "ai_desc" not in st.session_state: st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布房源", "📊 数据管理"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("房源名称")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000)
        raw_desc = st.text_area("粘贴英文描述")
        if st.button("✨ 执行 AI 提取"): 
            st.session_state.ai_desc = call_ai_summary(raw_desc)
    with c2:
        final_desc = st.text_area("最终描述", value=st.session_state.ai_desc, height=200)
        pics = st.file_uploader("上传照片", accept_multiple_files=True)
        if st.button("🚀 确认发布", type="primary"):
            poster = create_poster(pics, title)
            if poster:
                buf = io.BytesIO(); poster.save(buf, format='JPEG')
                url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": title, "region": region, 
                           "rooms": rooms, "price": price, "poster-link": url, "description": final_desc, 
                           "views": 0, "is_featured": False}
                conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])]))
                st.success("发布成功！")

with tab2:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not df.empty:
            st.metric("总曝光量", int(df['views'].sum()) if 'views' in df.columns else 0)
            target = st.selectbox("选择操作房源", df['title'].tolist())
            ca, cb, cc = st.columns(3)
            if ca.button("🔄 Refresh (刷新日期)"):
                df.loc[df['title'] == target, 'date'] = datetime.now().strftime("%Y-%m-%d")
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            is_f = df.loc[df['title'] == target, 'is_featured'].values[0] if 'is_featured' in df.columns else False
            if cb.button("🌟 切换精选状态"):
                df.loc[df['title'] == target, 'is_featured'] = not is_f
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            if cc.button("🗑️ 确认下架"):
                conn.update(worksheet="Sheet1", data=df[df['title'] != target]); st.rerun()
            st.dataframe(df)
    except: st.info("暂无数据")
