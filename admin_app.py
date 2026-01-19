import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import os
import requests
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary & DeepSeek 配置 (从 Secrets 读取)
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] # 这里假设你填的是 DeepSeek 的 Key

# --- 2. 核心函数：生成 6 宫格海报 ---
def create_poster(files, title_text):
    try:
        # 创建 800x1200 的纯白画布
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 加载字体 (确保仓库有 simhei.ttf)
        try:
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
        except:
            font_title = ImageFont.load_default()
            font_footer = ImageFont.load_default()

        # 处理前 6 张图片 (2列3行)
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB')
            # 缩放并裁剪为 390x300
            img = img.resize((390, 300), Image.Resampling.LANCZOS)
            x = 5 + (i % 2) * 395
            y = 5 + (i // 2) * 305
            canvas.paste(img, (x, y))

        # 底部写入标题
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        
        # 画一条装饰线
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        
        return canvas
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 3. 核心函数：DeepSeek AI 提取 (提示词已优化) ---
def call_ai_summary(raw_text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
        # 优化后的 Prompt：明确要求保留可用日期，剔除杂项
        prompt = (
            "你是一个专业的伦敦房产经纪助手。请将以下房源描述翻译并精简成中文要点：\n"
            "1. 必须包含 'Available date' (起租日期)。\n"
            "2. 使用✔符号开头，列出交通、周边生活、装修亮点。\n"
            "3. 严格禁止包含以下内容：Deposit (押金)、Min. Tenancy (租期)、Let type (租赁类型)、Long term/Short term。\n"
            "4. 语言要高级且吸引人。\n\n"
            f"原始描述如下：\n{raw_text}"
        )
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败，请手动编辑。错误: {e}"

# --- 4. 主界面布局 ---
st.title("🏡 Hao Harbour 房源发布与管理")

# 初始化 Session State 用于预览
if "ai_desc" not in st.session_state: st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布新房源", "🗂️ 房源管理 (删除)"])

# --- TAB 1: 发布房源 ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 填写基本信息")
        title = st.text_input("房源名称 (如: Merino Gardens)")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000, step=100)
        
        raw_desc = st.text_area("粘贴英文原始描述 (用于 AI 提取)", height=200)
        if st.button("✨ 执行 AI 智能提取"):
            if raw_desc:
                with st.spinner("DeepSeek 正在分析中..."):
                    st.session_state.ai_desc = call_ai_summary(raw_desc)
            else:
                st.warning("请先粘贴英文描述")

    with col2:
        st.subheader("2. 预览与发布")
        # AI 提取后的结果，允许手动微调
        final_desc = st.text_area("最终 Description (可微调)", value=st.session_state.ai_desc, height=250)
        
        photos = st.file_uploader("上传照片 (前6张将生成海报)", accept_multiple_files=True)
        
        if st.button("🚀 确认发布 (生成海报并同步)", type="primary"):
            if not title or not photos or not final_desc:
                st.error("请确保标题、描述和图片已准备就绪")
            else:
                with st.spinner("正在生成海报并上传云端..."):
                    # 生成海报
                    poster_img = create_poster(photos, title)
                    if poster_img:
                        # 转为字节流上传
                        buf = io.BytesIO()
                        poster_img.save(buf, format='JPEG')
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        p_url = upload_res.get("secure_url")
                        
                        # 同步 Google Sheets (追加模式)
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                            
                            new_data = {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "title": title,
                                "region": region,
                                "rooms": rooms,
                                "price": price,
                                "poster-link": p_url,
                                "description": final_desc
                            }
                            updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                            conn.update(worksheet="Sheet1", data=updated_df)
                            
                            st.success(f"✅ 《{title}》 已成功追加至数据库！")
                            st.image(p_url, caption="生成的海报已同步至客户端", width=400)
                        except Exception as e:
                            st.error(f"数据库同步失败: {e}")

# --- TAB 2: 房源管理 (删除) ---
with tab2:
    st.subheader("📋 现有房源在线列表")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        manage_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if manage_df.empty:
            st.info("暂无在线房源")
        else:
            # 删除功能
            to_delete = st.multiselect("选择要下架(删除)的房源标题", options=manage_df['title'].tolist())
            
            if st.button("🗑️ 确认下架选中房源"):
                if to_delete:
                    # 过滤掉要删除的行
                    new_df = manage_df[~manage_df['title'].isin(to_delete)]
                    conn.update(worksheet="Sheet1", data=new_df)
                    st.success(f"已下架: {len(to_delete)} 套房源")
                    st.rerun()
                else:
                    st.warning("请先选择房源")
            
            # 展示数据
            st.dataframe(manage_df[['date', 'title', 'region', 'rooms', 'price']], use_container_width=True)
            
    except Exception as e:
        st.error(f"列表加载失败: {e}")
