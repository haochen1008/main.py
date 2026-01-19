import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 1. 页面与云端配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] 

# --- 2. 核心合成引擎：6宫格 + 水印 ---
def create_poster(files, title_text):
    try:
        # 创建画布 800x1200
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 字体加载
        try:
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
            font_wm = ImageFont.truetype("simhei.ttf", 80)
        except:
            font_title = font_footer = font_wm = ImageFont.load_default()

        # 拼接前6张图
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            x = 5 + (i % 2) * 395
            y = 5 + (i // 2) * 305
            canvas.paste(img, (x, y))

        # 绘制防盗水印层
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_layer)
        wm_draw.text((180, 450), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        # 绘制底部标题区域
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        
        return canvas
    except Exception as e:
        st.error(f"合成失败: {e}")
        return None

# --- 3. AI 智能提取 ---
def call_ai(text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"请将以下房源翻译并精简为中文要点，必须含Available date，✔开头，严禁提到押金：\n{text}"
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
        res = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=20)
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取超时，请手动输入。"

# --- 4. 管理界面 ---
if "ai_out" not in st.session_state: st.session_state.ai_out = ""

tab1, tab2 = st.tabs(["🆕 房源录入", "📊 运营管理"])

with tab1:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("基础信息")
        title = st.text_input("房源名称 (如: Thames City)")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000)
        raw_txt = st.text_area("粘贴英文描述 (用于AI提取)")
        if st.button("✨ 执行 AI 智能提取"):
            st.session_state.ai_out = call_ai(raw_txt)
    
    with col_r:
        st.subheader("海报与发布")
        final_desc = st.text_area("最终描述 (用于展示)", value=st.session_state.ai_out, height=180)
        pics = st.file_uploader("上传照片 (合成前6张)", accept_multiple_files=True)
        if st.button("🚀 立即合成并发布", type="primary"):
            if not title or not pics: st.error("请完整填写标题并上传图片")
            else:
                with st.spinner("正在合成高画质海报..."):
                    poster = create_poster(pics, title)
                    if poster:
                        buf = io.BytesIO(); poster.save(buf, format='JPEG')
                        img_url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "title": title, "region": region, "rooms": rooms, "price": price,
                            "poster-link": img_url, "description": final_desc,
                            "views": 0, "is_featured": False
                        }
                        conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])]))
                        st.success("发布成功！海报已同步至云端。")

with tab2:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not df.empty:
            st.metric("网站总点击量", int(df['views'].sum()) if 'views' in df.columns else 0)
            target = st.selectbox("选择要操作的房源", df['title'].tolist())
            c1, c2, c3 = st.columns(3)
            if c1.button("🔄 刷新置顶"):
                df.loc[df['title'] == target, 'date'] = datetime.now().strftime("%Y-%m-%d")
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            
            is_f = df.loc[df['title'] == target, 'is_featured'].values[0] if 'is_featured' in df.columns else False
            f_btn = "⭐ 取消精选" if is_f else "🌟 设为精选"
            if c2.button(f_btn):
                df.loc[df['title'] == target, 'is_featured'] = not is_f
                conn.update(worksheet="Sheet1", data=df); st.rerun()
                
            if c3.button("🗑️ 确认下架"):
                conn.update(worksheet="Sheet1", data=df[df['title'] != target]); st.rerun()
            st.dataframe(df)
    except: st.info("暂无在线数据。")
