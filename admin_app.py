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

# --- 1. 初始化配置 ---
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
def call_smart_ai(text):
    if not text: return "✓ 请输入描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "作为房产专家，总结为中文列表。每行✓开头，保留楼盘和地铁站名。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "✓ 解析失败，请手动修改"

# --- 4. 核心：海报引擎 (双水印 & 加深版) ---
def create_poster(files, title, price):
    try:
        # 1200x1800 高清画布
        canvas = Image.new('RGB', (1200, 1800), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        try:
            font_title = ImageFont.truetype("simhei.ttf", 65)
            font_footer = ImageFont.truetype("simhei.ttf", 38)
            font_wm = ImageFont.truetype("simhei.ttf", 130) # 水印字体
        except:
            font_title = font_footer = font_wm = ImageFont.load_default()

        # A. 6 宫格拼接
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((590, 450), Image.Resampling.LANCZOS)
            x = 7 + (i % 2) * 597
            y = 7 + (i // 2) * 457
            canvas.paste(img, (x, y))

        # B. 双居中加深水印 (一上一下)
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_layer)
        
        # 水印颜色加深 (RGBA 的 A 值调高到 160)
        wm_color = (255, 255, 255, 160) 
        
        # 上水印
        wm_draw.text((220, 400), "Hao Harbour", font=font_wm, fill=wm_color)
        # 下水印
        wm_draw.text((220, 900), "Hao Harbour", font=font_wm, fill=wm_color)
        
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        # C. 底部信息排版 (移除日期)
        # 标题与价格
        display_text = f"{title} | GBP {price}/PCM | {rooms}"
        draw.text((60, 1460), display_text, font=font_title, fill=(0, 0, 0))
        
        # 装饰金色线条
        draw.line([(60, 1550), (1140, 1550)], fill=(200, 200, 200), width=3)
        
        # 副标题 (London Excellence)
        draw.text((60, 1585), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        # 底部微信
        draw.text((60, 1650), f"WeChat: HaoHarbour", font=font_footer, fill=(130, 130, 130))
        
        return canvas
    except Exception as e:
        st.error(f"海报生成出错: {e}")
        return None

# --- 5. 主程序逻辑 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布新房源", "⚙️ 管理与统计"])
    
    with t1:
        st.subheader("1. 基础信息")
        c1, c2, c3, c4 = st.columns(4)
        p_name = c1.text_input("房源名称")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        p_rooms = c4.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
        
        en_desc = st.text_area("英文原始描述")
        if st.button("🪄 AI 生成中文文案"):
            st.session_state['zh_content'] = call_smart_ai(en_desc)
        
        zh_desc = st.text_area("最终展示描述", value=st.session_state.get('zh_content', ''), height=150)
        up_imgs = st.file_uploader("上传房源图 (建议6张)", accept_multiple_files=True)
        
        if up_imgs:
            preview_img = create_poster(up_imgs, p_name, p_price)
            if preview_img:
                st.image(preview_img, caption="双水印强化海报预览", width=450)
                
                if st.button("🚀 立即发布"):
                    with st.spinner("同步云端中..."):
                        buf = BytesIO()
                        preview_img.save(buf, format="JPEG", quality=95)
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        img_url = upload_res['secure_url']
                        
                        now = datetime.now().strftime("%Y-%m-%d")
                        ws.append_row([now, p_name, p_reg, p_rooms, int(p_price), img_url, zh_desc, 0, 0])
                        st.success("发布成功！海报已存档。")
                        st.rerun()

    with t2:
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.metric("累计访问量", int(pd.to_numeric(df['views'], errors='coerce').sum()))
            search = st.text_input("🔍 快速搜索房源...").lower()
            f_df = df[df['title'].astype(str).str.lower().str.contains(search)] if search else df
            
            for i, row in f_df.iterrows():
                idx = i + 2
                with st.expander(f"{row['title']} (浏览: {row.get('views',0)})"):
                    with st.form(f"edit_{idx}"):
                        ca, cb, cc, cd = st.columns(4)
                        nt = ca.text_input("标题", row['title'])
                        np = cb.number_input("价格", value=int(float(row['price'] or 0)))
                        nr = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=0)
                        nrm = cd.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], index=0)
                        nd = st.text_area("文案", value=row['description'], height=100)
                        isf = st.checkbox("精选置顶", value=bool(row.get('is_featured', 0)))
                        
                        s1, s2 = st.columns(2)
                        if s1.form_submit_button("保存"):
                            ws.update(f"A{idx}:I{idx}", [[row['date'], nt, nr, nrm, np, row['poster-link'], nd, row['views'], 1 if isf else 0]])
                            st.rerun()
                        if s2.form_submit_button("删除"):
                            ws.delete_rows(idx)
                            st.rerun()
