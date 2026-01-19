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

# 配置 Cloudinary
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
            # 尝试加载中文字体，若失败则用默认
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
            font_watermark = ImageFont.truetype("simhei.ttf", 80)
        except:
            font_title = ImageFont.load_default()
            font_footer = ImageFont.load_default()
            font_watermark = ImageFont.load_default()

        # 处理前 6 张图片
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB')
            img = img.resize((390, 300), Image.Resampling.LANCZOS)
            x = 5 + (i % 2) * 395
            y = 5 + (i // 2) * 305
            canvas.paste(img, (x, y))

        # 绘制水印
        watermark_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(watermark_layer)
        wm_text = "Hao Harbour"
        bbox = wm_draw.textbbox((0, 0), wm_text, font=font_watermark)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        wm_draw.text(((800-w)/2, (900-h)/2), wm_text, font=font_watermark, fill=(255, 255, 255, 128))
        watermark_layer = watermark_layer.rotate(30, expand=False)
        canvas.paste(watermark_layer, (0, 0), watermark_layer)

        # 底部信息
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        return canvas
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 3. DeepSeek AI 提取函数 ---
def call_ai_summary(raw_text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
        prompt = (
            "你是一个专业的伦敦房产经纪助手。请将以下房源描述翻译并精简成中文要点：\n"
            "1. 必须包含 'Available date'。\n2. 使用✔符号开头。\n3. 禁止包含押金、租期要求等。\n\n"
            f"原始描述如下：\n{raw_text}"
        )
        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取遇到问题: {e}"

# --- 4. 主界面逻辑 ---
if "ai_desc" not in st.session_state:
    st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布新房源", "📊 数据看板 & 管理"])

# --- TAB 1: 发布房源 ---
with tab1:
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("1. 填写信息")
        title = st.text_input("房源名称")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000, step=100)
        raw_desc = st.text_area("粘贴英文原始描述", height=200)
        if st.button("✨ 执行 AI 提取"):
            if raw_desc:
                with st.spinner("AI 正在思考..."):
                    st.session_state.ai_desc = call_ai_summary(raw_desc)
            else:
                st.warning("请先输入英文描述")

    with col_right:
        st.subheader("2. 预览与发布")
        final_desc = st.text_area("最终描述 (可手动修改)", value=st.session_state.ai_desc, height=200)
        photos = st.file_uploader("上传照片", accept_multiple_files=True)
        if st.button("🚀 确认发布并同步", type="primary"):
            if not title or not photos:
                st.error("标题和图片不能为空")
            else:
                with st.spinner("处理海报中..."):
                    poster_img = create_poster(photos, title)
                    if poster_img:
                        buf = io.BytesIO()
                        poster_img.save(buf, format='JPEG')
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        p_url = upload_res.get("secure_url")
                        
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                            new_row = {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "title": title,
                                "region": region,
                                "rooms": rooms,
                                "price": price,
                                "poster-link": p_url,
                                "description": final_desc,
                                "views": 0 # 初始化浏览量
                            }
                            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                            conn.update(worksheet="Sheet1", data=updated_df)
                            st.success("✅ 发布成功！")
                            st.image(p_url, width=300)
                        except Exception as e:
                            st.error(f"同步失败: {e}")

# --- TAB 2: 管理与统计 ---
with tab2:
    st.subheader("📈 房源热度统计")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        manage_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not manage_df.empty:
            # 安全检查 views 列是否存在
            if 'views' not in manage_df.columns:
                manage_df['views'] = 0
            
            # 数据看板
            m1, m2 = st.columns(2)
            m1.metric("网站总曝光 (总点击次数)", int(manage_df['views'].sum()))
            m2.metric("在线房源总数", len(manage_df))
            
            # 排行图表
            st.write("### 房源热度排行")
            chart_data = manage_df[['title', 'views']].sort_values(by='views', ascending=False)
            st.bar_chart(chart_data.set_index('title'))
            
            st.divider()
            
            # 删除功能
            to_delete = st.multiselect("下架房源", options=manage_df['title'].tolist())
            if st.button("🗑️ 确认下架"):
                if to_delete:
                    new_df = manage_df[~manage_df['title'].isin(to_delete)]
                    conn.update(worksheet="Sheet1", data=new_df)
                    st.success("下架成功")
                    st.rerun()
            
            # 详细表格
            st.dataframe(manage_df, use_container_width=True)
        else:
            st.info("暂无房源数据")
    except Exception as e:
        st.error(f"加载看板失败: {e}")
