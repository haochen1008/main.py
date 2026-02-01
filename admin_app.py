import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- 1. 隐藏右上角 GitHub/Deploy 菜单 (强制 UI 纯净版) ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

st.markdown("""
    <style>
    /* 隐藏右上角 GitHub 图标、Deploy 按钮、以及三杠菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    /* 调整页面顶部空白 */
    .block-container {padding-top: 1rem;}
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

# --- 3. DeepSeek AI 逻辑 (禁止加粗 + ✓ 符号) ---
def call_deepseek(text):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个高端中介。请提取英文描述为中文。要求：禁止使用任何 Markdown 加粗符号（如 **）。每行开头必须使用符号 '✓ '。内容要包含卖点、交通、配套。语气专业。"
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=25
        )
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except: return "AI 暂时离线，请手动输入文案"

# --- 4. 紧凑型六图海报引擎 (45° 显性水印) ---
def create_compact_poster(files, title, price, wechat_id="HaoHarbour"):
    # 创建 1080x1600 紧凑版
    poster = Image.new("RGBA", (1080, 1600), (255, 255, 255, 255))
    
    # 拼图 (6张图)
    imgs = [Image.open(f).convert("RGBA").resize((535, 410)) for f in files[:6]]
    positions = [(2, 2), (542, 2), (2, 414), (542, 414), (2, 826), (542, 826)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 45° 显性水印 (灰度半透明)
    wm_layer = Image.new("RGBA", (2200, 2200), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
    for y in range(0, 2200, 280):
        draw_wm.text((0, y), wm_text, fill=(150, 150, 150, 60)) 
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-500, -500), wm_layer)

    # 底部紧凑信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1240, 1080, 1600], fill=(26, 28, 35, 255)) 
    draw.text((60, 1280), f"PREMIUM: {title}", fill=(191, 160, 100, 255))
    draw.text((60, 1360), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((60, 1460), f"WECHAT: {wechat_id}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 5. 管理界面逻辑 ---
ws = get_ws()
if ws:
    df = pd.DataFrame(ws.get_all_records())
    tab_add, tab_manage = st.tabs(["✨ 发布房源 & 海报", "⚙️ 房源库全维度管理"])

    with tab_add:
        st.subheader("1. 录入房源")
        c1, c2, c3 = st.columns(3)
        new_title = c1.text_input("房源名称")
        new_price = c2.number_input("租金", min_value=0)
        # 恢复东西南北中伦敦选项
        new_reg = c3.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        new_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
        en_desc = st.text_area("粘贴英文描述 (用于 AI 提取)")
        
        if st.button("🪄 智能生成中文文案 (Tick版)"):
            st.session_state['zh_temp'] = call_deepseek(en_desc)
        
        zh_desc = st.text_area("编辑确认文案", value=st.session_state.get('zh_temp', ''), height=150)

        st.subheader("2. 生成海报 (上传6张图)")
        uploaded_files = st.file_uploader("选择房源图片", accept_multiple_files=True, type=['jpg','png'])
        if uploaded_files and st.button("🎨 生成紧凑型水印海报"):
            final_poster = create_compact_poster(uploaded_files, new_title, new_price)
            st.image(final_poster, caption="预览生成效果 (45°水印)")
            buf = BytesIO()
            final_poster.save(buf, format="JPEG", quality=95)
            st.download_button("📥 下载海报", buf.getvalue(), "poster.jpg")

    with tab_manage:
        st.subheader("📊 房源全字段编辑 & 搜索")
        search_query = st.text_input("🔍 搜索名称或区域", "").lower()
        
        filtered_df = df.copy()
        if search_query:
            filtered_df = df[df['title'].str.lower().str.contains(search_query) | df['region'].str.lower().str.contains(search_query)]

        for i, row in filtered_df.iterrows():
            real_idx = i + 2 
            with st.expander(f"{'⭐' if row['is_featured'] else ''} 编辑: {row['title']}"):
                with st.form(f"edit_form_{i}"):
                    ca, cb, cc = st.columns(3)
                    e_name = ca.text_input("房源名称", value=row['title'])
                    e_price = cb.number_input("价格", value=int(row['price']))
                    # 恢复编辑状态下的区域选择
                    e_reg = cc.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']))
                    
                    e_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], index=["Studio", "1房", "2房", "3房", "4房+"].index(row['rooms']))
                    e_desc = st.text_area("中文文案", value=row['description'])
                    e_poster = st.text_input("封面图链接", value=row['poster-link'])
                    
                    f1, f2, f3 = st.columns(3)
                    is_feat = f1.checkbox("设为精选", value=bool(row['is_featured']))
                    if st.form_submit_button("💾 保存修改"):
                        ws.update(f"A{real_idx}:G{real_idx}", [[e_name, e_reg, e_price, e_rooms, e_desc, e_poster, 1 if is_feat else 0]])
                        st.success("已更新")
                        st.rerun()
                    if f3.form_submit_button("🗑️ 删除房源"):
                        ws.delete_rows(real_idx)
                        st.rerun()
