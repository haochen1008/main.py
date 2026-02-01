import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 深度隐藏 UI & 样式定制 ---
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
        st.error("数据库连接异常，请检查 Secrets 配置。")
        return None

# --- 3. 智能文案逻辑 (地名/地铁站保留英文) ---
def call_deepseek_smart(text):
    if not text: return "✓ 请输入英文描述"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个伦敦房产专家。任务：将输入英文总结为中文列表。要求：必须保留楼盘名、地铁站、街道名为英文名，不要翻译。禁止加粗**。每行'✓ '开头。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except:
        return "✓ 文案处理超时，请手动编辑。"

# --- 4. 强力水印海报逻辑 ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    poster = Image.new("RGBA", (800, 1100), (255, 255, 255, 255))
    # 缩小单图尺寸以换取 Base64 长度安全
    imgs = [Image.open(f).convert("RGBA").resize((398, 320)) for f in files[:6]]
    positions = [(1, 1), (401, 1), (1, 322), (401, 322), (1, 643), (401, 643)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 绘制金色显性大水印
    wm_layer = Image.new("RGBA", (1600, 1600), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 1600, 140):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE    " * 3, fill=(191, 160, 100, 160)) 
    poster.paste(wm_layer.rotate(45), (-300, -300), wm_layer.rotate(45))

    # 底部信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 965, 800, 1100], fill=(20, 22, 28, 255)) 
    draw.text((40, 985), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((40, 1040), f"RENTAL: £{price} /mo", fill=(255, 255, 255, 255))
    return poster.convert("RGB")

# --- 5. 极致压缩 Base64 (攻克 50,000 字符报错) ---
def get_safe_b64(img):
    quality = 40
    img = img.resize((750, 1030), Image.Resampling.LANCZOS)
    while quality > 5:
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        if len(b64_str) < 49000: return b64_str # 确保低于 Sheets 上限
        quality -= 5
    return None

# --- 6. 管理后台全逻辑 ---
ws = get_ws()
if ws:
    t1, t2 = st.tabs(["✨ 发布新房源", "⚙️ 搜索与维护库"])
    
    with t1:
        st.subheader("1. 基础资料录入")
        c1, c2, c3 = st.columns(3)
        p_name = c1.text_input("房源名称 (如: Harcourt Tower)")
        p_price = c2.number_input("月租 (£)", min_value=0)
        p_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        # --- 找回“几房”选项 ---
        p_rooms = st.selectbox("户型选择", ["Studio", "1房", "2房", "3房", "4房+"])
        
        en_desc = st.text_area("英文原文描述 (AI 会保留地名英文)")
        if st.button("🪄 智能混合解析"):
            st.session_state['zh_final'] = call_deepseek_smart(en_desc)
        zh_desc = st.text_area("最终文案确认", value=st.session_state.get('zh_final', ''), height=150)

        st.subheader("2. 生成海报并发布")
        up_imgs = st.file_uploader("上传 6 张房源照片", accept_multiple_files=True)
        if up_imgs:
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="45° 强化金色水印预览")
            
            if st.button("🚀 生成并直接发布"):
                b64_res = get_safe_b64(p_img)
                if b64_res:
                    try:
                        # 写入 Sheets
                        ws.append_row([p_name, p_reg, p_price, p_rooms, zh_desc, b64_res, 0, datetime.now().strftime("%Y-%m-%d")])
                        st.success("✅ 发布成功！海报已塞入数据库。")
                    except Exception as e:
                        st.error(f"写入失败: {e}")
                else:
                    st.error("海报编码依然超限，请尝试减少文案字数。")

    with t2:
        st.subheader("📊 房源全字段维护")
        # --- 修复搜索功能 ---
        # 必须先拉取最新数据，确保搜索是对当前数据的实时反馈
        df = pd.DataFrame(ws.get_all_records())
        search_q = st.text_input("🔍 输入房源名称搜索...", key="search_box").lower()
        
        if search_q:
            f_df = df[df['title'].astype(str).str.lower().str.contains(search_q, na=False)]
        else:
            f_df = df

        for i, row in f_df.iterrows():
            # 获取在全表中的真实行号
            real_idx = i + 2
            with st.expander(f"编辑: {row['title']}"):
                with st.form(f"form_edit_{real_idx}"):
                    ca, cb, cc = st.columns(3)
                    e_title = ca.text_input("房源名", row['title'])
                    
                    # --- 修复逻辑崩溃 ---
                    raw_p = row.get('price', 0)
                    try:
                        clean_p = int(float(raw_p)) if raw_p and str(raw_p).strip() else 0
                    except:
                        clean_p = 0
                    e_price = cb.number_input("租金", value=clean_p)
                    e_reg = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], 
                                         index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']) if row['region'] in ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"] else 0)
                    
                    e_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], 
                                           index=["Studio", "1房", "2房", "3房", "4房+"].index(row['rooms']) if row['rooms'] in ["Studio", "1房", "2房", "3房", "4房+"] else 0)
                    e_desc = st.text_area("文案内容", value=row['description'], height=120)
                    e_feat = st.checkbox("置顶精选", value=bool(row['is_featured']))
                    
                    col_save, col_del = st.columns([1,1])
                    if col_save.form_submit_button("💾 保存全部修改"):
                        ws.update(f"A{real_idx}:G{real_idx}", [[e_title, e_reg, e_price, e_rooms, e_desc, row['poster-link'], 1 if e_feat else 0]])
                        st.success("已同步至云端")
                        st.rerun()
                    if col_del.form_submit_button("🗑️ 彻底删除"):
                        ws.delete_rows(real_idx)
                        st.rerun()
