import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 深度隐藏 UI ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    .block-container {padding-top: 1rem;}
    .stButton>button {width: 100%; background-color: #bfa064; color: white; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据库连接 ---
def get_ws():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds).open("Hao_Harbour_DB").get_worksheet(0)
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

# --- 3. 智能文案逻辑 (地名/地铁站保留英文) ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个伦敦房产专家。任务：将输入英文总结为中文列表。要求：必须保留楼盘名、地铁站、街道名为英文。禁止加粗**。每行'✓ '开头。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 文案处理中..."

# --- 4. 强力巨型水印海报逻辑 ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    # 稍微缩小原始画布以适应数据限制
    poster = Image.new("RGBA", (900, 1200), (255, 255, 255, 255))
    imgs = [Image.open(f).convert("RGBA").resize((448, 340)) for f in files[:6]]
    positions = [(1, 1), (451, 1), (1, 342), (451, 342), (1, 683), (451, 683)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 绘制高清晰特大金色水印
    wm_layer = Image.new("RGBA", (2000, 2000), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
    for y in range(0, 2000, 150):
        draw_wm.text((0, y), wm_text, fill=(191, 160, 100, 140)) 
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-400, -400), wm_layer)

    # 底部信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1025, 900, 1200], fill=(20, 22, 28, 255)) 
    draw.text((40, 1045), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((40, 1095), f"RENTAL: £{price} /mo", fill=(255, 255, 255, 255))
    draw.text((40, 1145), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 5. 暴力压缩函数 (确保通过 50,000 限制) ---
def get_final_safe_b64(img):
    # 缩小尺寸是减小 Base64 体积最有效的办法
    target_width = 800
    w_percent = (target_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
    
    quality = 45
    while quality > 5:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        # 预留一点 Buffer，设为 48000
        if len(b64_str) < 48000:
            return b64_str
        quality -= 5
    return None

# --- 6. 管理后台全逻辑 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布新房源", "⚙️ 搜索与维护库"])
    with t1:
        st.subheader("1. 录入资料")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称 (如: Harcourt Tower)")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        en_desc = st.text_area("英文描述 (AI 会保留关键名词英文)")
        if st.button("🪄 AI 解析提取"):
            st.session_state['smart_zh'] = call_deepseek_smart(en_desc)
        zh_desc = st.text_area("最终文案确认", value=st.session_state.get('smart_zh', ''), height=150)

        st.subheader("2. 生成并发布")
        up_imgs = st.file_uploader("上传6张照片", accept_multiple_files=True)
        if up_imgs:
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="预览 (水印已大幅强化)")
            
            if st.button("🚀 生成并发布"):
                b64_res = get_final_safe_b64(p_img)
                if b64_res:
                    try:
                        new_row = [p_name, p_reg, p_price, "房源", zh_desc, b64_res, 0, datetime.now().strftime("%Y-%m-%d")]
                        ws.append_row(new_row)
                        st.success("✅ 发布成功！海报已塞入数据库。")
                    except Exception as e:
                        st.error(f"写入失败: {e}")
                else:
                    st.error("海报编码依然超限，请尝试减少文案字数。")

    with t2:
        st.subheader("📊 房源搜索与编辑")
        search_q = st.text_input("🔍 输入房源名称搜索...")
        all_data = ws.get_all_records()
        df = pd.DataFrame(all_data)
        f_df = df[df['title'].str.contains(search_q, na=False)] if search_q else df
        for i, row in f_df.iterrows():
            idx = i + 2
            with st.expander(f"编辑: {row['title']}"):
                with st.form(f"form_{idx}"):
                    c_a, c_b = st.columns(2)
                    en = c_a.text_input("名", row['title'])
                    ep = c_b.number_input("租 (£)", value=int(row['price']) if row['price'] else 0)
                    ed = st.text_area("文案", row['description'])
                    if st.form_submit_button("💾 保存同步"):
                        ws.update(f"A{idx}:G{idx}", [[en, row['region'], ep, row['rooms'], ed, row['poster-link'], row['is_featured']]])
                        st.rerun()
                    if st.form_submit_button("🗑️ 彻底删除"):
                        ws.delete_rows(idx)
                        st.rerun()
