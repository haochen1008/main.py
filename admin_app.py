import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw, ImageFont
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
from datetime import datetime

# --- 1. 初始化配置 (Cloudinary & UI) ---
cloudinary.config(
    cloud_name = st.secrets["cloudinary"]["cloud_name"],
    api_key = st.secrets["cloudinary"]["api_key"],
    api_secret = st.secrets["cloudinary"]["api_secret"]
)

st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stAppDeployButton {display:none;} header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
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

# --- 3. AI 文案解析 ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "作为伦敦房产专家，将房源描述总结为中文列表。保留楼盘、地铁站英文名。每行以✓开头，禁止加粗。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 解析失败，请手动输入"

# --- 4. 高画质微信水印海报生成 ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    # 使用 1200x1650 保证画质
    poster = Image.new("RGBA", (1200, 1650), (255, 255, 255, 255))
    imgs = [Image.open(f).convert("RGBA").resize((598, 480), Image.Resampling.LANCZOS) for f in files[:6]]
    positions = [(1, 1), (601, 1), (1, 482), (601, 482), (1, 963), (601, 963)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 45度金色强化水印
    wm_layer = Image.new("RGBA", (2000, 2000), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 2000, 150):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE    " * 4, fill=(191, 160, 100, 100)) 
    poster.paste(wm_layer.rotate(45), (-400, -400), wm_layer.rotate(45))

    # 底部黑色信息带 (带微信)
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1445, 1200, 1650], fill=(20, 22, 28, 255)) 
    draw.text((60, 1460), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((60, 1520), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((60, 1580), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    return poster.convert("RGB")

# --- 5. 主程序逻辑 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布新房源", "⚙️ 管理与流量统计"])
    
    with t1:
        st.subheader("1. 录入基本资料")
        c1, c2, c3, c4 = st.columns(4)
        p_name = c1.text_input("房源名称 (title)")
        p_price = c2.number_input("月租金 (price)", min_value=0)
        p_reg = c3.selectbox("区域 (region)", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        p_rooms = c4.selectbox("户型 (rooms)", ["Studio", "1房", "2房", "3房", "4房+"])
        
        en_desc = st.text_area("粘贴英文描述 (用于 AI 提取)")
        if st.button("🪄 AI 智能提取中文文案"):
            st.session_state['zh_content'] = call_deepseek_smart(en_desc)
        
        zh_desc = st.text_area("最终展示描述", value=st.session_state.get('zh_content', ''), height=150)
        up_imgs = st.file_uploader("上传 6 张房源图片", accept_multiple_files=True)
        
        if up_imgs:
            preview_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(preview_img, caption="高画质水印海报预览", width=400)
            
            if st.button("🚀 生成并直接发布房源"):
                with st.spinner("上传高画质海报至 Cloudinary..."):
                    buf = BytesIO()
                    preview_img.save(buf, format="JPEG", quality=95)
                    upload_res = cloudinary.uploader.upload(buf.getvalue())
                    img_url = upload_res['secure_url']
                    
                    # 写入 Sheet (顺序: date, title, region, rooms, price, poster-link, description, views, is_featured)
                    now = datetime.now().strftime("%Y-%m-%d")
                    ws.append_row([now, p_name, p_reg, p_rooms, p_price, img_url, zh_desc, 0, 0])
                    st.success("发布成功！图片已存至 Cloudinary。")
                    st.rerun()

    with t2:
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty:
            st.metric("总访问量 (Views)", int(pd.to_numeric(df['views'], errors='coerce').sum()))
            
            search_q = st.text_input("🔍 搜索房源名称...").lower()
            f_df = df[df['title'].astype(str).str.lower().str.contains(search_q)] if search_q else df
            
            for i, row in f_df.iterrows():
                idx = i + 2
                with st.expander(f"编辑: {row['title']} (浏览: {row.get('views',0)})"):
                    with st.form(f"edit_{idx}"):
                        ca, cb, cc, cd = st.columns(4)
                        new_t = ca.text_input("标题", row['title'])
                        new_p = cb.number_input("价格", value=int(float(row['price'] or 0)))
                        new_r = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=0)
                        new_rm = cd.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], index=0)
                        new_d = st.text_area("描述内容", value=row['description'], height=100)
                        is_f = st.checkbox("置顶精选", value=bool(row.get('is_featured', 0)))
                        
                        cs, cd = st.columns(2)
                        if cs.form_submit_button("💾 保存更新"):
                            # 更新 A-I 列内容
                            ws.update(f"A{idx}:I{idx}", [[row['date'], new_t, new_r, new_rm, new_p, row['poster-link'], new_d, row['views'], 1 if is_f else 0]])
                            st.success("更新成功")
                            st.rerun()
                        if cd.form_submit_button("🗑️ 删除房源"):
                            ws.delete_rows(idx)
                            st.rerun()
