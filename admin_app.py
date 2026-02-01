import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 深度 UI 隐藏 (隐藏 GitHub/Deploy/Share) ---
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

# --- 3. 智能混合文案 (保留地名/地铁站英文) ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入英文描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个伦敦房产专家。总结房源为中文列表。保留楼盘名、地铁站、街道名为英文。禁止加粗**。每行'✓ '开头。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 文案处理中..."

# --- 4. 强力水印海报 + 极致压缩 (解决 APIError) ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    poster = Image.new("RGBA", (800, 1100), (255, 255, 255, 255))
    imgs = [Image.open(f).convert("RGBA").resize((398, 320)) for f in files[:6]]
    positions = [(1, 1), (401, 1), (1, 322), (401, 322), (1, 643), (401, 643)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])
    wm_layer = Image.new("RGBA", (1600, 1600), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 1600, 140):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE    " * 3, fill=(191, 160, 100, 160)) 
    poster.paste(wm_layer.rotate(45), (-300, -300), wm_layer.rotate(45))
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 965, 800, 1100], fill=(20, 22, 28, 255)) 
    draw.text((40, 980), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((40, 1030), f"RENTAL: £{price} /mo", fill=(255, 255, 255, 255))
    return poster.convert("RGB")

def get_safe_b64(img):
    quality = 40
    img = img.resize((700, 960), Image.Resampling.LANCZOS)
    while quality > 5:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        if len(b64_str) < 49000: return b64_str # 严格死守 50,000 字符限制
        quality -= 5
    return None

# --- 5. 主程序 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布房源", "⚙️ 搜索与编辑"])
    
    with t1:
        st.subheader("1. 录入信息")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称")
        p_price = c2.number_input("租金 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        # --- 补回“几房”选项 ---
        p_rooms = st.selectbox("户型 (户型将准确存入数据库)", ["Studio", "1房", "2房", "3房", "4房+"])
        
        en_desc = st.text_area("英文描述 (AI保留地名英文)")
        if st.button("🪄 智能提取文案"):
            st.session_state['smart_zh'] = call_deepseek_smart(en_desc)
        zh_desc = st.text_area("文案预览", value=st.session_state.get('smart_zh', ''), height=120)

        up_imgs = st.file_uploader("上传6张图", accept_multiple_files=True)
        if up_imgs:
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="金色水印预览")
            if st.button("🚀 强制发布"):
                b64 = get_safe_b64(p_img)
                if b64:
                    # 严格列顺序：Title, Region, Price, Rooms, Description, Poster-Link, Is_Featured, Date
                    ws.append_row([p_name, p_reg, p_price, p_rooms, zh_desc, b64, 0, datetime.now().strftime("%Y-%m-%d")])
                    st.success("✅ 发布成功！")
                    st.rerun() # 发布后刷新以更新管理列表

    with t2:
        st.subheader("📊 搜索与维护")
        # 实时拉取最新数据
        raw_data = ws.get_all_records()
        df = pd.DataFrame(raw_data)
        
        search_q = st.text_input("🔍 搜索名称...", key="search_bar").lower()
        
        # 修复搜索逻辑：确保是对标题进行字符串匹配
        if not df.empty and 'title' in df.columns:
            f_df = df[df['title'].astype(str).str.lower().str.contains(search_q, na=False)]
        else:
            f_df = df

        for i, row in f_df.iterrows():
            # 确定在 Google Sheets 中的行号 (数据从第2行开始)
            idx = i + 2
            with st.expander(f"编辑: {row.get('title', '未知房源')}"):
                with st.form(f"f_{idx}"):
                    ca, cb, cc = st.columns(3)
                    en = ca.text_input("房源名", row.get('title', ''))
                    
                    # 修复租金读取报错
                    try:
                        cur_p = int(float(row.get('price', 0))) if row.get('price') else 0
                    except: cur_p = 0
                    ep = cb.number_input("租金", value=cur_p)
                    
                    er = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], 
                                      index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']) if row.get('region') in ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"] else 0)
                    
                    # 户型编辑
                    erm = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], 
                                       index=["Studio", "1房", "2房", "3房", "4房+"].index(row['rooms']) if row.get('rooms') in ["Studio", "1房", "2房", "3房", "4房+"] else 0)
                    
                    ed = st.text_area("文案内容", value=row.get('description', ''), height=120)
                    ef = st.checkbox("设为精选", value=bool(row.get('is_featured', 0)))
                    
                    col_s, col_d = st.columns([1,1])
                    if col_s.form_submit_button("💾 保存同步"):
                        # 严格按照表格 A-G 列顺序更新
                        ws.update(f"A{idx}:G{idx}", [[en, er, ep, erm, ed, row.get('poster-link', ''), 1 if ef else 0]])
                        st.success("已保存")
                        st.rerun()
                    if col_d.form_submit_button("🗑️ 删除"):
                        ws.delete_rows(idx)
                        st.rerun()
