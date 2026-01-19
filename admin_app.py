import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 配置与连接 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"]

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
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(wm_layer).text((180, 450), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        return canvas
    except Exception: return None

# --- 主界面 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 快捷管理"])

with tab1:
    c1, c2 = st.columns(2)
    if "ai_out" not in st.session_state: st.session_state.ai_out = ""
    with c1:
        t_title = st.text_input("标题")
        t_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        t_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        t_price = st.number_input("月租 (£)", value=3000)
        t_raw = st.text_area("描述原文")
        if st.button("✨ AI 提取"):
            try:
                res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                                    headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, 
                                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": f"简要提取中文亮点：{t_raw}"}]})
                st.session_state.ai_out = res.json()['choices'][0]['message']['content']
            except: st.error("AI 接口连接失败")
    with c2:
        t_desc = st.text_area("最终描述", value=st.session_state.ai_out, height=200)
        t_pics = st.file_uploader("上传照片", accept_multiple_files=True)
        if st.button("🚀 发布", type="primary"):
            p = create_poster(t_pics, t_title)
            if p:
                buf = io.BytesIO(); p.save(buf, format='JPEG')
                url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_data = pd.DataFrame([{"date": datetime.now().strftime("%Y-%m-%d"), "title": t_title, "region": t_reg, "rooms": t_room, "price": t_price, "poster-link": url, "description": t_desc, "views": 0, "is_featured": False}])
                conn.update(worksheet="Sheet1", data=pd.concat([df, new_data]))
                st.success("发布成功")

with tab2:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not df.empty:
            target = st.selectbox("🎯 选择房源进行管理", df['title'].tolist())
            row = df[df['title'] == target].iloc[0]
            
            # 操作按钮
            b1, b2, b3 = st.columns(3)
            if b1.button("🔄 Refresh (置顶)", use_container_width=True):
                df.loc[df['title'] == target, 'date'] = datetime.now().strftime("%Y-%m-%d")
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            if b2.button("🌟 切换精选", use_container_width=True):
                df.loc[df['title'] == target, 'is_featured'] = not row.get('is_featured', False)
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            if b3.button("🗑️ 下架房源", use_container_width=True):
                conn.update(worksheet="Sheet1", data=df[df['title'] != target]); st.rerun()
            
            # 编辑表单
            with st.form("edit_form"):
                st.write("### 📝 修改房源信息")
                e_price = st.number_input("价格", value=int(row['price']) if pd.notnull(row['price']) else 0)
                e_desc = st.text_area("描述内容", value=row.get('description', ''), height=150)
                if st.form_submit_button("💾 保存修改", type="primary"):
                    df.loc[df['title'] == target, ['price', 'description']] = [e_price, e_desc]
                    conn.update(worksheet="Sheet1", data=df); st.success("已更新"); st.rerun()
    except Exception as e:
        st.error(f"连接数据库出错: {str(e)}")
