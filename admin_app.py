import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] 

# --- 2. 核心函数：生成 6 宫格海报 (带水印) ---
def create_poster(files, title_text):
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try:
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
            font_watermark = ImageFont.truetype("simhei.ttf", 80)
        except:
            font_title = ImageFont.load_default()
            font_footer = ImageFont.load_default()
            font_watermark = ImageFont.load_default()

        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB')
            img = img.resize((390, 300), Image.Resampling.LANCZOS)
            x = 5 + (i % 2) * 395
            y = 5 + (i // 2) * 305
            canvas.paste(img, (x, y))

        # 绘制半透明水印
        watermark_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(watermark_layer)
        wm_text = "Hao Harbour"
        bbox = wm_draw.textbbox((0, 0), wm_text, font=font_watermark)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        wm_draw.text(((800-w)/2, (900-h)/2), wm_text, font=font_watermark, fill=(255, 255, 255, 128))
        watermark_layer = watermark_layer.rotate(30, expand=False)
        canvas.paste(watermark_layer, (0, 0), watermark_layer)

        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        return canvas
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 3. DeepSeek AI 提取 ---
def call_ai_summary(raw_text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
        prompt = (
            "你是一个专业的伦敦房产经纪助手。请将以下房源描述翻译并精简成中文要点：\n"
            "1. 必须包含 'Available date'。\n2. 使用✔符号开头。\n3. 禁止包含押金等信息。\n\n"
            f"原始描述如下：\n{raw_text}"
        )
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败: {e}"

# --- 4. 主界面布局 ---
if "ai_desc" not in st.session_state: st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布新房源", "📊 管理与统计"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("1. 填写房源信息")
        title = st.text_input("房源名称")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000, step=100)
        raw_desc = st.text_area("粘贴英文描述", height=200)
        if st.button("✨ 执行 AI 智能提取"):
            if raw_desc:
                with st.spinner("AI 提取中..."):
                    st.session_state.ai_desc = call_ai_summary(raw_desc)
    with col2:
        st.subheader("2. 预览与发布")
        final_desc = st.text_area("最终描述", value=st.session_state.ai_desc, height=200)
        photos = st.file_uploader("上传照片", accept_multiple_files=True)
        if st.button("🚀 确认发布", type="primary"):
            if not title or not photos:
                st.error("请确保标题和图片已上传")
            else:
                with st.spinner("处理中..."):
                    poster_img = create_poster(photos, title)
                    if poster_img:
                        buf = io.BytesIO(); poster_img.save(buf, format='JPEG')
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        p_url = upload_res.get("secure_url")
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                            new_data = {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "title": title, "region": region, "rooms": rooms, "price": price,
                                "poster-link": p_url, "description": final_desc,
                                "views": 0, "is_featured": False
                            }
                            updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                            conn.update(worksheet="Sheet1", data=updated_df)
                            st.success(f"✅ 《{title}》已成功追加！")
                        except Exception as e:
                            st.error(f"同步失败: {e}")

with tab2:
    st.subheader("📋 房源热度统计")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        manage_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        if not manage_df.empty:
            st.metric("网站总点击量", int(manage_df['views'].sum()) if 'views' in manage_df.columns else 0)
            
            st.write("### ⚙️ 管理操作")
            target = st.selectbox("选择目标房源", options=manage_df['title'].tolist())
            c1, c2, c3 = st.columns(3)
            
            if c1.button("🔄 Refresh (刷新置顶)", use_container_width=True):
                manage_df.loc[manage_df['title'] == target, 'date'] = datetime.now().strftime("%Y-%m-%d")
                conn.update(worksheet="Sheet1", data=manage_df)
                st.rerun()

            is_feat = manage_df.loc[manage_df['title'] == target, 'is_featured'].values[0] if 'is_featured' in manage_df.columns else False
            if c2.button("🌟/⭐ 切换精选状态", use_container_width=True):
                manage_df.loc[manage_df['title'] == target, 'is_featured'] = not is_feat
                conn.update(worksheet="Sheet1", data=manage_df)
                st.rerun()

            if c3.button("🗑️ 确认删除", use_container_width=True):
                new_df = manage_df[manage_df['title'] != target]
                conn.update(worksheet="Sheet1", data=new_df)
                st.rerun()

            st.dataframe(manage_df, use_container_width=True)
        else: st.info("暂无数据")
    except Exception as e: st.error(f"数据加载失败: {e}")
