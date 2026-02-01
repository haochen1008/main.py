import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. UI 隐藏与样式 (彻底隐藏 GitHub 按钮) ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stAppDeployButton {display:none;} header {visibility: hidden;}
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

# --- 3. 极致压缩逻辑 (解决 50,000 字符报错) ---
def get_safe_b64(img):
    quality = 40
    img = img.resize((720, 1000), Image.Resampling.LANCZOS) # 强制调整尺寸
    while quality > 5:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        if len(b64_str) < 48500: # 严格死守 Google 限制
            return b64_str
        quality -= 5
    return None

# --- 4. 强力水印海报逻辑 (带微信) ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    poster = Image.new("RGBA", (800, 1100), (255, 255, 255, 255))
    imgs = [Image.open(f).convert("RGBA").resize((398, 320)) for f in files[:6]]
    positions = [(1, 1), (401, 1), (1, 322), (401, 322), (1, 643), (401, 643)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 45度金色强化水印
    wm_layer = Image.new("RGBA", (1600, 1600), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 1600, 140):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE    " * 3, fill=(191, 160, 100, 160)) 
    poster.paste(wm_layer.rotate(45), (-300, -300), wm_layer.rotate(45))

    # 底部黑色信息带
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 965, 800, 1100], fill=(20, 22, 28, 255)) 
    draw.text((40, 975), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((40, 1015), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((40, 1055), f"WECHAT: {wechat}", fill=(191, 160, 100, 255)) # 补回微信信息
    
    return poster.convert("RGB")

# --- 5. 文案解析 ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "伦敦房产专家。总结为中文列表，保留楼盘、地铁站英文。禁止加粗。每行✓开头。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 解析中..."

# --- 6. 管理后台全逻辑 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布新房源", "⚙️ 管理与流量统计"])
    
    with t1:
        st.subheader("1. 录入资料")
        c1, c2, c3, c4 = st.columns(4)
        p_name = c1.text_input("名称 (title)")
        p_price = c2.number_input("月租 (price)", min_value=0)
        p_reg = c3.selectbox("区域 (region)", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        p_rooms = c4.selectbox("户型 (rooms)", ["Studio", "1房", "2房", "3房", "4房+"])
        
        en_desc = st.text_area("英文描述 (AI解析)")
        if st.button("🪄 AI 解析提取"):
            st.session_state['smart_zh'] = call_deepseek_smart(en_desc)
        zh_desc = st.text_area("最终描述 (description)", value=st.session_state.get('smart_zh', ''), height=120)

        up_imgs = st.file_uploader("上传6张图", accept_multiple_files=True)
        if up_imgs:
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="带微信水印海报预览")
            if st.button("🚀 强制发布"):
                b64 = get_safe_b64(p_img)
                if b64:
                    # 严格遵循列顺序: date, title, region, rooms, price, poster_link, poster-link, description, views, is_featured
                    now = datetime.now().strftime("%Y-%m-%d")
                    ws.append_row([now, p_name, p_reg, p_rooms, p_price, "", b64, zh_desc, 0, 0])
                    st.success("发布成功！")
                    st.rerun()

    with t2:
        df = pd.DataFrame(ws.get_all_records())
        
        # --- 流量统计展示 ---
        if not df.empty and 'views' in df.columns:
            st.subheader("📈 流量统计")
            st.metric("网站总点击量 (Total Views)", int(pd.to_numeric(df['views'], errors='coerce').sum()))
            st.divider()

        st.subheader("🔍 房源搜索与维护")
        search_q = st.text_input("输入标题搜索...", key="search_bar").lower()
        f_df = df[df['title'].astype(str).str.lower().str.contains(search_q, na=False)] if search_q else df

        for i, row in f_df.iterrows():
            idx = i + 2
            with st.expander(f"编辑: {row.get('title')} (点击量: {row.get('views', 0)})"):
                with st.form(f"f_{idx}"):
                    ca, cb, cc, cd = st.columns(4)
                    en = ca.text_input("标题", row.get('title'))
                    
                    # 修复租金读取报错
                    try: cur_p = int(float(row.get('price', 0)))
                    except: cur_p = 0
                    ep = cb.number_input("租金", value=cur_p)
                    
                    er = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], 
                                      index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row.get('region')) if row.get('region') in ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"] else 0)
                    erm = cd.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], 
                                       index=["Studio", "1房", "2房", "3房", "4房+"].index(row.get('rooms')) if row.get('rooms') in ["Studio", "1房", "2房", "3房", "4房+"] else 0)
                    
                    ed = st.text_area("描述", value=row.get('description', ''), height=120)
                    isf = st.checkbox("设为精选", value=bool(row.get('is_featured', 0)))
                    
                    c_save, c_del = st.columns(2)
                    if c_save.form_submit_button("💾 保存同步"):
                        # 严格更新 A-J: date, title, region, rooms, price, poster_link, poster-link, description, views, is_featured
                        vals = [[row.get('date'), en, er, erm, ep, row.get('poster_link'), row.get('poster-link'), ed, row.get('views'), 1 if isf else 0]]
                        ws.update(f"A{idx}:J{idx}", vals)
                        st.success("已更新")
                        st.rerun()
                    if c_del.form_submit_button("🗑️ 删除"):
                        ws.delete_rows(idx)
                        st.rerun()
