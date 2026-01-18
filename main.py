import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import os
import re
import pandas as pd
from datetime import datetime

# --- 配置：云端环境下字体路径处理 ---
def load_font(size):
    # GitHub 上我们会把 simhei.ttf 放在根目录
    font_path = "simhei.ttf"
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

# --- 核心逻辑（保留你最满意的防截断与AI提取逻辑） ---
def call_ai_summary(desc):
    API_KEY = "sk-d99a91f22bf340139a335fb3d50d0ef5"
    API_URL = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = (
        "你是一个伦敦高端房产文案专家。请将房源信息提取为中文，条目不少于12条：\n"
        "1. 标题：英文原名。\n"
        "2. 租金：月租与周租（月租XXXX磅，周租XXX磅）。\n"
        "3. 地理位置与交通：保留英文原名，不翻译地址、地铁站名和线名。\n"
        "4. 高校通勤：列举便捷通勤的高校 (LSE, KCL, UCL, IC, King's)，禁止具体分钟数。\n"
        "要求：每行以 '√' 开头，专有名词不翻译，严禁备注。"
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
    fill = (20, 20, 20, 220) 
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
    
    # 拼图
    for i in range(num_imgs):
        img = Image.open(images[i]).convert("RGB")
        tw = (canvas_w - gap * 3) // 2
        scale = max(tw/img.width, img_h/img.height)
        img = img.resize((int(img.width*scale), int(img.height*scale)), Image.Resampling.LANCZOS)
        left, top = (img.width-tw)/2, (img.height-img_h)/2
        poster.paste(img.crop((left, top, left+tw, top+img_h)), (gap if i%2==0 else tw+gap*2, (i//2)*(img_h+gap)+gap))

    # 排版
    font, cur_y = load_font(48), rows*(img_h+gap)+120
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        content = re.sub(r'^[√\-v*]\s*', '', line)
        wrapped = pixel_wrap(content, font, 920)
        for idx, part in enumerate(wrapped):
            if idx == 0 and line.startswith('√'):
                points = [(100, cur_y + 24), (100 + 10, cur_y + 48), (100 + 32, cur_y + 12)]
                draw.line(points, fill=(35,35,35), width=6)
            draw.text((180 if line.startswith('√') else 100, cur_y), part, fill=(35,35,35), font=font)
            cur_y += 90
        cur_y += 25
    
    res_poster = poster.crop((0, 0, canvas_w, cur_y + 150))
    return add_deep_watermark(res_poster, "Hao Harbour")

# --- 4. 网页布局与云端显示 ---
st.set_page_config(page_title="Hao Harbour Online", layout="wide")
st.title("🏡 Hao Harbour 在线房源管理系统")

# 侧边栏：用于展示在线版说明
st.sidebar.info("在线版：生成的房源将实时分类。")
reg = st.sidebar.selectbox("选择区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
rm = st.sidebar.selectbox("选择房型", ["1房", "2房", "3房", "4房+"])
price = st.sidebar.number_input("月租 (£/pcm)", value=3000)

desc = st.text_area("粘贴 Description")
files = st.file_uploader("上传图片 (前8张)", accept_multiple_files=True)

if st.button("🚀 生成在线海报"):
    if desc and files:
        with st.spinner("AI 正在云端排版..."):
            poster_img = create_poster(files[:8], call_ai_summary(desc))
            st.image(poster_img)
            
            # 提供下载
            buf = io.BytesIO()
            poster_img.convert('RGB').save(buf, format='PNG')
            st.download_button("📥 下载海报", buf.getvalue(), f"{reg}_{rm}_{price}.png")
