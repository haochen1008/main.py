import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 彻底隐藏 Streamlit 官方 UI ---
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

# --- 2. 数据库连接 ---
def get_ws():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds).open("Hao_Harbour_DB").get_worksheet(0)

# --- 3. DeepSeek AI 逻辑 (✓ 开头，去加粗) ---
def call_deepseek(text):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个专业房产中介。请提取英文描述。要求：禁止使用 **。每行开头必须使用 '✓ '。语气高级。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 请手动录入文案"

# --- 4. 增强版海报引擎 (显性 45° 水印 + 紧凑布局) ---
def create_final_poster(files, title, price, wechat="HaoHarbour"):
    # 采用紧凑的 1080x1500 布局
    poster = Image.new("RGBA", (1080, 1500), (255, 255, 255, 255))
    
    # 六图拼接
    imgs = [Image.open(f).convert("RGBA").resize((538, 410)) for f in files[:6]]
    positions = [(1, 1), (541, 1), (1, 412), (541, 412), (1, 823), (541, 823)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # --- 显性水印逻辑 (关键修复) ---
    wm_layer = Image.new("RGBA", (2500, 2500), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 5
    # 使用较深的金色并降低透明度，确保在浅色背景也清晰
    for y in range(0, 2500, 220):
        draw_wm.text((0, y), wm_text, fill=(191, 160, 100, 90)) 
    wm_layer = wm_layer.rotate(45)
    # 将水印中心对准海报中心
    poster.paste(wm_layer, (-600, -600), wm_layer)

    # 底部紧凑信息栏
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1235, 1080, 1500], fill=(20, 22, 28, 255)) 
    draw.text((50, 1260), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((50, 1325), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((50, 1390), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 5. 图片转 Base64 (实现一键发布) ---
def img_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

# --- 6. 管理界面逻辑 ---
ws = get_ws()
if ws:
    df = pd.DataFrame(ws.get_all_records())
    t1, t2 = st.tabs(["✨ 一键发布房源", "⚙️ 全维度管理"])

    with t1:
        st.subheader("1. 录入基本信息")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("所属区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        p_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
        en_desc = st.text_area("英文原文 (用于 AI 提取)")
        
        if st.button("🪄 智能解析文案"):
            st.session_state['zh_fix'] = call_deepseek(en_desc)
        
        final_zh = st.text_area("确认中文文案", value=st.session_state.get('zh_fix', ''), height=120)

        st.subheader("2. 生成海报并发布")
        up_files = st.file_uploader("上传6张照片", accept_multiple_files=True)
        
        if up_files:
            # 自动实时生成预览
            p_img = create_final_poster(up_files, p_name, p_price)
            st.image(p_img, caption="水印预览")
            
            if st.button("🚀 生成并一键发布"):
                if p_name and final_zh:
                    with st.spinner("正在发布到 Client 端..."):
                        # 直接将图片转为 DataURL 存入数据库
                        img_data = img_to_base64(p_img)
                        new_row = [p_name, p_reg, p_price, p_rooms, final_zh, img_data, 0, datetime.now().strftime("%Y-%m-%d")]
                        ws.append_row(new_row)
                        st.success("✅ 发布成功！海报已同步至前台。")
                else:
                    st.error("请完整填写名称和文案后再发布")

    with t2:
        st.subheader("📊 房源全字段管理")
        q = st.text_input("🔍 搜索名称...").lower()
        f_df = df[df['title'].str.lower().str.contains(q)] if q else df
        
        for i, row in f_df.iterrows():
            idx = i + 2
            with st.expander(f"编辑: {row['title']}"):
                with st.form(f"f_{i}"):
                    ca, cb, cc = st.columns(3)
                    en = ca.text_input("房源名", row['title'])
                    er = cb.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']))
                    ep = cc.number_input("租金", value=int(row['price']))
                    
                    ed = st.text_area("描述", row['description'])
                    is_f = st.checkbox("设为精选", value=bool(row['is_featured']))
                    
                    c_save, c_del = st.columns([1,1])
                    if c_save.form_submit_button("💾 保存"):
                        ws.update(f"A{idx}:G{idx}", [[en, er, ep, row['rooms'], ed, row['poster-link'], 1 if is_f else 0]])
                        st.success("修改成功")
                        st.rerun()
                    if c_del.form_submit_button("🗑️ 删除"):
                        ws.delete_rows(idx)
                        st.rerun()
