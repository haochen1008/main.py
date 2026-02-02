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

# --- 4. 融合后的海报生成引擎 (保留你喜欢的 Version 2 设计) ---
def create_poster(files, title, price):
    try:
        # 统一比例：1200x1800 高画质画布
        canvas = Image.new('RGB', (1200, 1800), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 加载字体 (针对中文字体做了 fallback 处理)
        try:
            # 尝试加载中文字体，如果是在 Linux 容器运行，可能需要指定绝对路径
            font_title = ImageFont.truetype("simhei.ttf", 65)
            font_footer = ImageFont.truetype("simhei.ttf", 35)
            font_wm = ImageFont.truetype("simhei.ttf", 120)
        except:
            font_title = font_footer = font_wm = ImageFont.load_default()

        # 1. 6 宫格拼接 (Version 2 逻辑)
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((590, 450), Image.Resampling.LANCZOS)
            x = 7 + (i % 2) * 597
            y = 7 + (i // 2) * 457
            canvas.paste(img, (x, y))

        # 2. 30度旋转水印 (Version 2 标志性设计)
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_layer)
        wm_draw.text((250, 650), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        # 3. 底部信息排版 (Version 2 灰金线条风格)
        # 标题与价格
        display_text = f"{title} | £{price}/mo"
        draw.text((60, 1450), display_text, font=font_title, fill=(0, 0, 0))
        
        # 装饰线条
        draw.line([(60, 1540), (1140, 1540)], fill=(200, 200, 200), width=3)
        
        # 副标题
        draw.text((60, 1570), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        draw.text((60, 1630), f"WeChat: HaoHarbour  |  Date: {datetime.now().strftime('%Y-%m-%d')}", font=font_footer, fill=(150, 150, 150))
        
        return canvas
    except Exception as e:
        st.error(f"海报合成失败: {e}")
        return None

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
            # 使用融合后的新海报引擎
            preview_img = create_poster(up_imgs, p_name, p_price)
            if preview_img:
                st.image(preview_img, caption="高画质 Version 2 海报预览", width=450)
                
                if st.button("🚀 生成并直接发布房源"):
                    with st.spinner("上传海报至 Cloudinary..."):
                        buf = BytesIO()
                        preview_img.save(buf, format="JPEG", quality=95)
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        img_url = upload_res['secure_url']
                        
                        # 写入 Sheet (顺序: date, title, region, rooms, price, poster-link, description, views, is_featured)
                        now = datetime.now().strftime("%Y-%m-%d")
                        ws.append_row([now, p_name, p_reg, p_rooms, int(p_price), img_url, zh_desc, 0, 0])
                        st.success("发布成功！海报已生成并存至云端。")
                        st.rerun()

    with t2:
        # (管理端逻辑保持不变，确保 F 列 poster-link 正确)
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
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
                        
                        cs, cd_btn = st.columns(2)
                        if cs.form_submit_button("💾 保存更新"):
                            ws.update(f"A{idx}:I{idx}", [[row['date'], new_t, new_r, new_rm, new_p, row['poster-link'], new_d, row['views'], 1 if is_f else 0]])
                            st.success("更新成功")
                            st.rerun()
                        if cd_btn.form_submit_button("🗑️ 删除房源"):
                            ws.delete_rows(idx)
                            st.rerun()
