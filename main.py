import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import requests
import io
import os
import re
import pandas as pd
from datetime import datetime

# --- 1. 初始化页面与云端连接 ---
st.set_page_config(page_title="Hao Harbour 房源管理旗舰版", layout="wide")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"云端连接异常: {e}")

# --- 2. 核心绘图与AI函数 (保持之前的完美排版逻辑) ---
def load_font(size):
    font_path = "simhei.ttf"
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def call_ai_summary(desc):
    # 此处建议将 API_KEY 也放入 Streamlit Secrets 以确保安全
    API_KEY = "sk-d99a91f22bf340139a335fb3d50d0ef5"
    API_URL = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = (
        "你是一个伦敦高端房产文案专家。请将房源信息提取为中文，条目不少于12条：\n"
        "1. 标题：英文原名。\n"
        "2. 租金：月租与周租（月租XXXX磅，周租XXX磅）。\n"
        "3. 地理位置与交通：保留英文原名，不要翻译地址、地铁站名和线名。\n"
        "4. 通勤描述：列举可便捷通勤至 LSE, KCL, UCL, IC, King's College 等名校，严禁写分钟数。\n"
        "要求：每行以 '√' 开头，专有名词不翻译。严禁备注说明。"
    )
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt + f"\n\n原文：{desc}"}], "temperature": 0.3}
    res = requests.post(API_URL, headers=headers, json=payload)
    return res.json()['choices'][0]['message']['content']

def pixel_wrap(text, font, max_pixel_width):
    lines, current_line = [], ""
    for char in text:
        test_line = current_line + char
        if font.getlength(test_line) <= max_pixel_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    return lines

def add_deep_watermark(image, text):
    img = image.convert('RGBA')
    w, h = img.size
    txt_layer = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    font = load_font(240)
    fill = (20, 20, 20, 220) # 极深水印
    temp_draw = ImageDraw.Draw(txt_layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    txt_img = Image.new('RGBA', (tw + 100, th + 100), (255, 255, 255, 0))
    ImageDraw.Draw(txt_img).text((50, 50), text, font=font, fill=fill)
    rotated = txt_img.rotate(22, expand=True, resample=Image.BICUBIC)
    rw, rh = rotated.size
    for i in range(1, 4):
        txt_layer.paste(rotated, (w//2 - rw//2, (h * i)//4 - rh//2), rotated)
    return Image.alpha_composite(img, txt_layer)

def create_poster(images, text):
    canvas_w, img_h, gap = 1200, 450, 25
    num_imgs = min(len(images), 8)
    rows = (num_imgs + 1) // 2
    poster = Image.new('RGB', (canvas_w, 15000), (255, 255, 255))
    draw = ImageDraw.Draw(poster)
    
    # 图片 2x4 布局
    for i in range(num_imgs):
        img = Image.open(images[i]).convert("RGB")
        tw = (canvas_w - gap * 3) // 2
        scale = max(tw/img.width, img_h/img.height)
        img = img.resize((int(img.width*scale), int(img.height*scale)), Image.Resampling.LANCZOS)
        left, top = (img.width-tw)/2, (img.height-img_h)/2
        poster.paste(img.crop((left, top, left+tw, top+img_h)), (gap if i%2==0 else tw+gap*2, (i//2)*(img_h+gap)+gap))

    # 文本排版（物理防截断）
    font, cur_y = load_font(48), rows*(img_h+gap)+120
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        content = re.sub(r'^[√\-v*]\s*', '', line)
        wrapped = pixel_wrap(content, font, 920)
        for idx, part in enumerate(wrapped):
            render_x = 180 if line.startswith('√') else 100
            if idx == 0 and line.startswith('√'):
                points = [(100, cur_y + 24), (110, cur_y + 48), (132, cur_y + 12)]
                draw.line(points, fill=(35,35,35), width=6)
            draw.text((render_x, cur_y), part, fill=(35,35,35), font=font)
            cur_y += 90
        cur_y += 25
    
    final_poster = poster.crop((0, 0, canvas_w, cur_y + 150))
    return add_deep_watermark(final_poster, "Hao Harbour")

# --- 3. 网页主逻辑 ---
st.title("🏡 Hao Harbour 房源管理系统")

# 侧边栏
mode = st.sidebar.radio("选择操作", ["✨ 生成并存入云端", "📚 浏览全伦敦库"])
st.sidebar.divider()
st.sidebar.info("归类标签设置")
reg = st.sidebar.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
rm = st.sidebar.selectbox("房型", ["1房", "2房", "3房", "4房+"])
price_pcm = st.sidebar.number_input("月租价格 (£/pcm)", value=3000, step=100)

if mode == "✨ 生成并存入云端":
    st.header("录入新房源")
    prop_title = st.text_input("房源名称 (如: Lexington Gardens)")
    desc = st.text_area("粘贴 Description")
    uploaded_files = st.file_uploader("上传照片 (前8张)", accept_multiple_files=True)

    if st.button("🚀 生成海报并保存数据"):
        if desc and uploaded_files and prop_title:
            with st.spinner("AI 正在提取亮点并排版..."):
                # 生成海报
                poster_img = create_poster(uploaded_files[:8], call_ai_summary(desc))
                st.image(poster_img)
                
                # 保存到云端表格
                try:
                    new_row = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "title": prop_title,
                        "region": reg,
                        "rooms": rm,
                        "price": price_pcm,
                        "poster_link": "Download from app" # 暂时标记
                    }])
                    old_df = conn.read(worksheet="Sheet1", ttl=0)
                    updated_df = pd.concat([old_df, new_row], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    st.success(f"✅ {prop_title} 已成功存档至云端表格！")
                    st.balloons()
                except Exception as e:
                    st.error(f"保存到云端失败: {e}")

                # 提供海报下载
                buf = io.BytesIO()
                poster_img.convert('RGB').save(buf, format='PNG')
                st.download_button("📥 点击下载高清海报", buf.getvalue(), f"{prop_title}.png")

else:
    st.header("📚 全伦敦房源归类汇总")
    try:
        db_df = conn.read(worksheet="Sheet1", ttl=0)
        
        # 筛选功能
        col1, col2 = st.columns(2)
        with col1:
            f_reg = st.multiselect("按区域筛选", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        with col2:
            f_rm = st.multiselect("按房型筛选", ["1房", "2房", "3房", "4房+"])
        
        filtered_df = db_df
        if f_reg: filtered_df = filtered_df[filtered_df['region'].isin(f_reg)]
        if f_rm: filtered_df = filtered_df[filtered_df['rooms'].isin(f_rm)]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # 简单统计
        st.caption(f"当前库中共收录 {len(filtered_df)} 套房源")
    except Exception as e:
        st.info("库中暂无数据，请先切换到生成模式进行录入。")
