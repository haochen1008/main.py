import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 强制 UI 隐藏 (GitHub/Deploy/Menu) ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    .block-container {padding-top: 1rem;}
    .stButton>button {width: 100%; background-color: #bfa064; color: white;}
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

# --- 3. DeepSeek 混合文案逻辑 (保留关键英文名词) ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        # 指令调整：保留楼盘名、地铁站、地名为英文
        prompt = "你是一个伦敦豪宅专家。请总结房源。要求：1.总结为中文。2.保留楼盘名称、地铁站名、区域地名为英文原名，不要翻译。3.禁止加粗**。4.每行开头用'✓ '。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 提取失败，请手动录入"

# --- 4. 强力大水印海报引擎 (紧凑型) ---
def create_strong_poster(files, title, price, wechat="HaoHarbour"):
    # 尺寸稍大以保证清晰度，但发布时会压缩
    poster = Image.new("RGBA", (1000, 1400), (255, 255, 255, 255))
    
    # 六图拼接
    imgs = [Image.open(f).convert("RGBA").resize((498, 380)) for f in files[:6]]
    positions = [(1, 1), (501, 1), (1, 382), (501, 382), (1, 763), (501, 763)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # --- 显性巨型水印 ---
    wm_layer = Image.new("RGBA", (2000, 2000), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
    for y in range(0, 2000, 160): # 160 间距更密
        draw_wm.text((0, y), wm_text, fill=(191, 160, 100, 140)) # 140 高不透明度
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-400, -400), wm_layer)

    # 底部信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1145, 1000, 1400], fill=(20, 22, 28, 255)) 
    draw.text((50, 1170), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((50, 1240), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((50, 1315), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 5. 图片压缩转换 (解决 API Error) ---
def img_to_safe_b64(img):
    buffered = BytesIO()
    # 降低质量以通过 Google Sheets 50k 字符限制
    img.save(buffered, format="JPEG", quality=45, optimize=True)
    return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"

# --- 6. 管理后台主逻辑 ---
ws = get_ws()
if ws:
    data_all = ws.get_all_records()
    df = pd.DataFrame(data_all)
    tab1, tab2 = st.tabs(["✨ 发布新房源", "⚙️ 管理房源库"])

    with tab1:
        st.subheader("1. 基础信息")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        p_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
        en_desc = st.text_area("英文原文描述 (AI 将保留关键地名英文)")
        
        if st.button("🪄 智能混合解析文案"):
            st.session_state['smart_zh'] = call_deepseek_smart(en_desc)
        
        zh_desc = st.text_area("中文文案确认", value=st.session_state.get('smart_zh', ''), height=150)

        st.subheader("2. 生成并发布")
        up_imgs = st.file_uploader("上传6张照片", accept_multiple_files=True)
        if up_imgs:
            p_img = create_strong_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="预览 (水印已大幅强化)")
            
            if st.button("🚀 生成并直接发布"):
                try:
                    b64_str = img_to_safe_b64(p_img)
                    if len(b64_str) > 50000:
                        st.error("图片还是太大了，请尝试上传更小的照片。")
                    else:
                        new_row = [p_name, p_reg, p_price, p_rooms, zh_desc, b64_str, 0, datetime.now().strftime("%Y-%m-%d")]
                        ws.append_row(new_row)
                        st.success("✅ 发布成功！")
                except Exception as e:
                    st.error(f"发布出错: {e}")

    with tab2:
        st.subheader("📊 房源全维度搜索与管理")
        search_q = st.text_input("🔍 搜索房源名称...").lower()
        f_df = df[df['title'].str.lower().str.contains(search_q)] if search_q else df
        
        for i, row in f_df.iterrows():
            idx = i + 2
            with st.expander(f"{'⭐' if row['is_featured'] else ''} 编辑: {row['title']}"):
                with st.form(f"edit_{idx}"):
                    c_a, c_b, c_c = st.columns(3)
                    e_title = c_a.text_input("名称", row['title'])
                    e_price = c_b.number_input("租金", value=int(row['price']))
                    e_reg = c_c.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']))
                    
                    e_desc = st.text_area("文案", value=row['description'], height=120)
                    is_f = st.checkbox("置顶精选", value=bool(row['is_featured']))
                    
                    col_s, col_d = st.columns([1,1])
                    if col_s.form_submit_button("💾 保存全部"):
                        ws.update(f"A{idx}:G{idx}", [[e_title, e_reg, e_price, row['rooms'], e_desc, row['poster-link'], 1 if is_f else 0]])
                        st.rerun()
                    if col_d.form_submit_button("🗑️ 删除"):
                        ws.delete_rows(idx)
                        st.rerun()
