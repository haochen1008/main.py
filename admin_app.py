import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from datetime import datetime

# --- 1. 强制隐藏 UI 元素 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据库与 AI 核心函数 ---
def get_ws():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds).open("Hao_Harbour_DB").get_worksheet(0)

def call_deepseek(text):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个高端中介。请提取英文描述为中文。要求：禁止使用 **。每行开头必须使用 '✓ '。内容包含卖点、交通、配套。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 请手动输入文案"

# --- 3. 极致紧凑海报引擎 (强化水印 + 零冗余布局) ---
def create_pro_poster(files, title, price, wechat="HaoHarbour"):
    # 比例调整为 1080x1500，极致紧凑
    poster = Image.new("RGBA", (1080, 1500), (255, 255, 255, 255))
    
    # 六图拼拼图
    imgs = [Image.open(f).convert("RGBA").resize((538, 410)) for f in files[:6]]
    positions = [(1, 1), (541, 1), (1, 412), (541, 412), (1, 823), (541, 823)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 45° 强化版水印 (金色半透明，提升可见度)
    wm_layer = Image.new("RGBA", (2200, 2200), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
    for y in range(0, 2200, 250):
        # 使用浅金色 (191, 160, 100) 增加可见度
        draw_wm.text((0, y), wm_text, fill=(191, 160, 100, 70)) 
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-500, -500), wm_layer)

    # 底部超紧凑信息栏
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1235, 1080, 1500], fill=(20, 22, 28, 255)) 
    # 调整文字行间距，极度紧凑
    draw.text((50, 1260), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((50, 1330), f"RENTAL: £{price} /mo", fill=(255, 255, 255, 255))
    draw.text((50, 1400), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 4. 管理界面逻辑 ---
ws = get_ws()
df = pd.DataFrame(ws.get_all_records())
tab_add, tab_manage = st.tabs(["✨ 发布新房源", "⚙️ 房源库全维度管理"])

with tab_add:
    st.subheader("1. 信息采集")
    c1, c2, c3 = st.columns(3)
    p_name = c1.text_input("房源名称")
    p_price = c2.number_input("租金", min_value=0)
    p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
    
    p_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
    en_desc = st.text_area("粘贴英文原文用于 AI 提取")
    
    if st.button("🪄 AI 生成文案"):
        st.session_state['zh_fix'] = call_deepseek(en_desc)
    
    final_zh = st.text_area("中文文案确认", value=st.session_state.get('zh_fix', ''), height=150)
    poster_url = st.text_input("海报链接 (请先将生成的海报上传至图床，然后将链接填入此处发布)")

    st.subheader("2. 海报合成预览")
    up_files = st.file_uploader("上传6张图", accept_multiple_files=True)
    if up_files:
        if st.button("🎨预览并下载紧凑海报"):
            p_img = create_pro_poster(up_files, p_name, p_price)
            st.image(p_img)
            buf = BytesIO()
            p_img.save(buf, format="JPEG")
            st.download_button("📥 点击下载海报", buf.getvalue(), "poster.jpg")

    if st.button("🚀 正式发布房源到 Client 端"):
        if p_name and poster_url:
            # 写入数据库: Title, Region, Price, Rooms, Description, Poster-Link, Is_Featured, Date
            new_row = [p_name, p_reg, p_price, p_rooms, final_zh, poster_url, 0, datetime.now().strftime("%Y-%m-%d")]
            ws.append_row(new_row)
            st.success("✅ 发布成功！客户现在可以在前台看到了。")
        else:
            st.error("请确保填写了房源名称和海报链接")

with tab_manage:
    st.subheader("📊 搜索与全字段编辑")
    q = st.text_input("🔍 快速搜索房源名称...").lower()
    f_df = df[df['title'].str.lower().str.contains(q)] if q else df
    
    for i, row in f_df.iterrows():
        idx = i + 2
        with st.expander(f"编辑: {row['title']}"):
            with st.form(f"f_{i}"):
                ca, cb, cc = st.columns(3)
                en = ca.text_input("名称", row['title'])
                er = cb.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']))
                ep = cc.number_input("价格", value=int(row['price']))
                
                ed = st.text_area("文案", row['description'])
                el = st.text_input("海报链接", row['poster-link'])
                is_f = st.checkbox("置顶精选", value=bool(row['is_featured']))
                
                c_save, c_del = st.columns([1,1])
                if c_save.form_submit_button("💾 保存"):
                    ws.update(f"A{idx}:G{idx}", [[en, er, ep, row['rooms'], ed, el, 1 if is_f else 0]])
                    st.rerun()
                if c_del.form_submit_button("🗑️ 删除"):
                    ws.delete_rows(idx)
                    st.rerun()
