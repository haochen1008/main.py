import streamlit as st
# ... 其他引用保持不变 ...

# --- 1. 云端配置 (增加 Key 存在性检查) ---
if "CLOUDINARY_CLOUD_NAME" in st.secrets:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )
else:
    st.error("❌ Cloudinary 配置未在 Secrets 中找到，请检查层级顺序！")
    st.stop() # 停止运行，防止后续崩溃

# ... 后续代码保持不变 ...
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import requests
import io
import os
import re
import pandas as pd
from datetime import datetime

# --- 1. 配置云端连接 ---
st.set_page_config(page_title="Hao Harbour 房源旗舰店", layout="wide")

# 配置 Cloudinary
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# 连接 Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"数据库连接失败: {e}")

# --- 2. 核心功能函数 ---
def load_font(size):
    font_path = "simhei.ttf"
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def call_ai_summary(desc):
    API_KEY = "sk-d99a91f22bf340139a335fb3d50d0ef5"
    API_URL = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = "你是一个伦敦房产专家。请提取房源信息为中文，每行以 '√' 开头，不少于12条。专有名词不翻译，严禁写通勤的具体分钟数。"
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt + f"\n\n原文：{desc}"}], "temperature": 0.3}
    res = requests.post(API_URL, headers=headers, json=payload)
    return res.json()['choices'][0]['message']['content']

def create_poster(images, text):
    # (此处省略你之前已经完美的绘图逻辑代码，请务必保留之前那套 create_poster 和 pixel_wrap 函数内容)
    # ... 请把你上一版 main.py 里的绘图代码粘贴在这里 ...
    return final_poster # 假设返回的是 PIL Image 对象

# --- 3. UI 界面 ---
st.title("🏡 Hao Harbour 房源管理系统")

# 侧边栏：核心设置
with st.sidebar:
    st.header("⚙️ 房源设置")
    reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
    rm = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
    price = st.number_input("月租 (£/pcm)", value=3000)
    st.divider()
    mode = st.radio("功能切换", ["✨ 生成新房源", "🖼️ 房源展示墙"])

if mode == "✨ 生成新房源":
    title = st.text_input("房源名称 (如: Lexington Gardens)")
    desc = st.text_area("房源描述 (Paste Description)")
    files = st.file_uploader("上传照片 (前8张)", accept_multiple_files=True)

    if st.button("🚀 生成海报并全自动存入云端"):
        if title and desc and files:
            with st.spinner("AI 文案提取 + 自动拼图 + 云端同步中..."):
                # 1. 生成海报
                poster_img = create_poster(files[:8], call_ai_summary(desc))
                
                # 2. 上传到 Cloudinary
                buf = io.BytesIO()
                poster_img.convert('RGB').save(buf, format='PNG')
                upload_res = cloudinary.uploader.upload(buf.getvalue(), folder="hao_harbour")
                cloud_url = upload_res["secure_url"]
                
                # 3. 写入 Google Sheets
                new_row = pd.DataFrame([{
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "title": title,
                    "region": reg,
                    "rooms": rm,
                    "price": price,
                    "poster_link": cloud_url
                }])
                old_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([old_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.image(cloud_url, caption="✅ 已成功同步至云端橱窗")
                st.balloons()

else:
    st.header("🖼️ 全伦敦房源橱窗")
    try:
        df = conn.read(worksheet="Sheet1", ttl=0)
        # 筛选逻辑
        f_reg = st.multiselect("按区域筛选", df['region'].unique())
        if f_reg: df = df[df['region'].isin(f_reg)]
        
        # 网格化展示 (重点美化部分)
        if not df.empty:
            cols = st.columns(3)
            for idx, row in df.iterrows():
                with cols[idx % 3]:
                    # 使用卡片式容器
                    with st.container(border=True):
                        st.image(row['poster_link'], use_container_width=True)
                        st.subheader(row['title'])
                        st.caption(f"📍 {row['region']} | 🏠 {row['rooms']} | 💰 £{row['price']}")
                        st.link_button("📥 查看/下载高清海报", row['poster_link'])
        else:
            st.info("库中暂无房源，快去生成第一个吧！")
    except:
        st.warning("暂无云端数据。")
