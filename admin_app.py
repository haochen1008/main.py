import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64
from datetime import datetime

# --- 1. 深度 UI 定制：隐藏所有 GitHub/Deploy 痕迹 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    .block-container {padding-top: 1rem;}
    /* 按钮样式优化 */
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #bfa064; color: white;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据库连接函数 ---
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

# --- 3. DeepSeek 逻辑：强制中文 + 符号清理 ---
def call_deepseek_chinese(text):
    if not text: return "✓ 请输入内容"
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        prompt = "你是一个伦敦豪宅中介。任务：将输入英文总结为中文。要求：1.必须使用中文。2.禁止加粗符号**。3.每行开头用'✓ '。4.含卖点、交通、配套。"
        r = requests.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}]},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=25)
        return r.json()['choices'][0]['message']['content'].replace("**", "")
    except Exception as e:
        return f"✓ AI 提取出错: {str(e)}"

# --- 4. 强力巨型水印海报引擎 ---
def create_massive_watermark_poster(files, title, price, wechat="HaoHarbour"):
    # 采用 1080x1500 紧凑版布局
    poster = Image.new("RGBA", (1080, 1500), (255, 255, 255, 255))
    
    # 六图拼接逻辑
    imgs = [Image.open(f).convert("RGBA").resize((538, 410)) for f in files[:6]]
    positions = [(1, 1), (541, 1), (1, 412), (541, 412), (1, 823), (541, 823)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # --- 强力巨型水印：双重金色渲染 ---
    wm_layer = Image.new("RGBA", (2500, 2500), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    # 增加字体不透明度 (130) 和 水印密度
    wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
    for y in range(0, 2500, 180): # 180 间距更密，覆盖更全
        draw_wm.text((0, y), wm_text, fill=(191, 160, 100, 130)) 
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-600, -600), wm_layer)

    # 底部信息区 (极致紧凑)
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1235, 1080, 1500], fill=(20, 22, 28, 255)) 
    draw.text((50, 1260), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
    draw.text((50, 1325), f"RENTAL: £{price} /month", fill=(255, 255, 255, 255))
    draw.text((50, 1395), f"WECHAT: {wechat}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 5. 主程序界面 ---
ws = get_ws()
if ws:
    # 缓存数据减少请求
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    tab1, tab2 = st.tabs(["✨ 发布新房源", "⚙️ 房源库全维度管理"])

    with tab1:
        st.subheader("1. 基础资料录入")
        col1, col2, col3 = st.columns(3)
        p_name = col1.text_input("房源名称 (如: Triptych Bankside)")
        p_price = col2.number_input("月租 (£)", min_value=0, step=50)
        # 找回区域选项
        p_reg = col3.selectbox("所属区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
        
        p_rooms = st.selectbox("户型选择", ["Studio", "1房", "2房", "3房", "4房+"])
        en_desc = st.text_area("粘贴英文描述用于 AI 解析", height=150)
        
        if st.button("🪄 智能生成中文文案"):
            with st.spinner("DeepSeek 正在翻译并总结..."):
                st.session_state['zh_content'] = call_deepseek_chinese(en_desc)
        
        zh_desc = st.text_area("最终中文文案确认", value=st.session_state.get('zh_content', ''), height=150)

        st.subheader("2. 水印海报生成 & 发布")
        up_imgs = st.file_uploader("请上传 6 张房源照片", accept_multiple_files=True, type=['jpg','png','jpeg'])
        
        if up_imgs:
            # 实时预览海报
            p_img = create_massive_watermark_poster(up_imgs, p_name, p_price)
            st.image(p_img, caption="45° 强力金色水印预览")
            
            # --- 一键发布功能 ---
            if st.button("🚀 生成并直接发布房源"):
                if p_name and zh_desc:
                    with st.spinner("正在上传至数据库..."):
                        # 图片转 Base64 存储
                        buf = BytesIO()
                        p_img.save(buf, format="JPEG")
                        b64_data = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
                        
                        # 写入 Google Sheets
                        new_row = [p_name, p_reg, p_price, p_rooms, zh_desc, b64_data, 0, datetime.now().strftime("%Y-%m-%d")]
                        ws.append_row(new_row)
                        st.success("✅ 发布成功！海报已同步至 Client 端。")
                else:
                    st.warning("请确保名称和文案已填写")

    with tab2:
        st.subheader("📊 房源全字段管理")
        # 找回搜索功能
        search_q = st.text_input("🔍 搜索名称或区域...").lower()
        f_df = df[df['title'].str.lower().str.contains(search_q) | df['region'].str.lower().str.contains(search_q)] if search_q else df
        
        for i, row in f_df.iterrows():
            real_idx = i + 2
            with st.expander(f"{'⭐' if row['is_featured'] else ''} 编辑: {row['title']}"):
                with st.form(f"edit_form_{i}"):
                    c_a, c_b, c_c = st.columns(3)
                    e_title = c_a.text_input("名称", row['title'])
                    e_price = c_b.number_input("价格", value=int(row['price']))
                    e_reg = c_c.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"], 
                                         index=["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"].index(row['region']))
                    
                    e_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"], 
                                          index=["Studio", "1房", "2房", "3房", "4房+"].index(row['rooms']))
                    e_desc = st.text_area("中文文案", value=row['description'], height=150)
                    e_feat = st.checkbox("设为精选 (Featured)", value=bool(row['is_featured']))
                    
                    col_save, col_del = st.columns([1,1])
                    if col_save.form_submit_button("💾 保存全部修改"):
                        # 保持 Poster-Link (row[5]) 不变
                        ws.update(f"A{real_idx}:G{real_idx}", [[e_title, e_reg, e_price, e_rooms, e_desc, row['poster-link'], 1 if e_feat else 0]])
                        st.success("已保存")
                        st.rerun()
                    if col_del.form_submit_button("🗑️ 彻底删除"):
                        ws.delete_rows(real_idx)
                        st.rerun()
