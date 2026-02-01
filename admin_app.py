import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 深度 UI 隐藏 ---
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
    except:
        return None

# --- 3. 智能文案 (保留核心英文) ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个伦敦豪宅专家。请总结房源。要求：保留楼盘名、地铁站、街道名为英文。禁止加粗**。每行'✓ '开头。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 文案处理中..."

# --- 4. 强力水印海报逻辑 ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    # 为了过审，初始画布调小
    poster = Image.new("RGBA", (800, 1100), (255, 255, 255, 255))
    imgs = [Image.open(f).convert("RGBA").resize((398, 320)) for f in files[:6]]
    positions = [(1, 1), (401, 1), (1, 322), (401, 322), (1, 643), (401, 643)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 巨型金色水印
    wm_layer = Image.new("RGBA", (1600, 1600), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 1600, 140):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE    " * 3, fill=(191, 160, 100, 160)) 
    poster.paste(wm_layer.rotate(45), (-300, -300), wm_layer.rotate(45))

    # 底部信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 965, 800, 1100], fill=(20, 22, 28, 255)) 
    draw.text((40, 980), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((40, 1030), f"RENTAL: £{price} /mo", fill=(255, 255, 255, 255))
    return poster.convert("RGB")

# --- 5. 极致压缩：死磕 50,000 限制 ---
def get_safe_b64(img):
    quality = 40
    img = img.resize((700, 960), Image.Resampling.LANCZOS) # 强制缩小分辨率
    while quality > 5:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        if len(b64_str) < 49000: return b64_str
        quality -= 5
    return None

# --- 6. 管理后台 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布房源", "⚙️ 搜索与编辑"])
    with t1:
        st.subheader("1. 信息录入")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        en_desc = st.text_area("英文描述")
        if st.button("🪄 AI 解析"):
            st.session_state['smart_zh'] = call_deepseek_smart(en_desc)
        zh_desc = st.text_area("文案确认", value=st.session_state.get('smart_zh', ''), height=120)

        up_imgs = st.file_uploader("上传6张图", accept_multiple_files=True)
        if up_imgs:
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="水印预览")
            if st.button("🚀 强制发布"):
                b64 = get_safe_b64(p_img)
                if b64:
                    ws.append_row([p_name, p_reg, p_price, "房源", zh_desc, b64, 0, datetime.now().strftime("%Y-%m-%d")])
                    st.success("✅ 发布成功！")
                else: st.error("海报太大，无法塞入表格")

    with t2:
        st.subheader("📊 搜索与维护")
        search_q = st.text_input("🔍 搜索名称...")
        df = pd.DataFrame(ws.get_all_records())
        # 修复搜索逻辑
        f_df = df[df['title'].astype(str).str.contains(search_q, na=False)] if search_q else df
        
        for i, row in f_df.iterrows():
            idx = i + 2
            with st.expander(f"编辑: {row['title']}"):
                with st.form(f"form_{idx}"):
                    c_a, c_b = st.columns(2)
                    en = c_a.text_input("名称", row['title'])
                    # --- 修复逻辑崩溃的关键点 ---
                    raw_val = row.get('price', 0)
                    try:
                        clean_price = int(float(raw_val)) if raw_val and str(raw_val).strip() else 0
                    except:
                        clean_price = 0
                    ep = c_b.number_input("租金", value=clean_price, key=f"p_{idx}")
                    
                    ed = st.text_area("文案", row['description'])
                    if st.form_submit_button("💾 保存"):
                        ws.update(f"A{idx}:E{idx}", [[en, row['region'], ep, row['rooms'], ed]])
                        st.rerun()
                    if st.form_submit_button("🗑️ 删除"):
                        ws.delete_rows(idx)
                        st.rerun()
