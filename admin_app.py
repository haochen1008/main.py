import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- 1. 数据库连接 ---
def get_ws():
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds).open("Hao_Harbour_DB").get_worksheet(0)

# --- 2. DeepSeek AI 逻辑 ---
def call_deepseek(text):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": "总结伦敦房源亮点为中文列表"}, {"role": "user", "content": text}]
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20
        )
        return r.json()['choices'][0]['message']['content']
    except: return "AI 暂时离线，请手动输入"

# --- 3. 六图海报引擎 (带 45° 水印) ---
def create_multi_photo_poster(files, title, price, wechat_id="HaoHarbour"):
    # 创建主画布 (1080x1920 高清竖版)
    poster = Image.new("RGBA", (1080, 1920), (255, 255, 255, 255))
    
    # 拼图逻辑：取前6张
    imgs = [Image.open(f).convert("RGBA").resize((530, 400)) for f in files[:6]]
    positions = [(5, 5), (545, 5), (5, 410), (545, 410), (5, 815), (545, 815)]
    for i, img in enumerate(imgs):
        poster.paste(img, positions[i])

    # 绘制 45° 倾斜全屏水印
    wm_layer = Image.new("RGBA", (2000, 2000), (0,0,0,0))
    draw_wm = ImageDraw.Draw(wm_layer)
    for y in range(0, 2000, 300):
        draw_wm.text((0, y), "HAO HARBOUR EXCLUSIVE  " * 5, fill=(255, 255, 255, 40))
    wm_layer = wm_layer.rotate(45)
    poster.paste(wm_layer, (-400, -400), wm_layer)

    # 底部信息区
    draw = ImageDraw.Draw(poster)
    draw.rectangle([0, 1400, 1080, 1920], fill=(26, 28, 35, 255))
    draw.text((60, 1450), f"Exclusive: {title}", fill=(191, 160, 100, 255))
    draw.text((60, 1550), f"Price: £{price} /mo", fill=(255, 255, 255, 255))
    draw.text((60, 1750), f"WeChat: {wechat_id}", fill=(191, 160, 100, 255))
    
    return poster.convert("RGB")

# --- 4. 管理后台界面 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
ws = get_ws()
df = pd.DataFrame(ws.get_all_records())

tab_add, tab_manage = st.tabs(["✨ 发布房源 & 海报", "⚙️ 房源库管理 (编辑/删除)"])

with tab_add:
    st.subheader("1. 录入信息")
    c1, c2 = st.columns(2)
    new_title = c1.text_input("房源名称")
    new_price = c2.number_input("租金", min_value=0)
    new_rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"]) # 找回完整户型
    en_desc = st.text_area("英文描述")
    
    if st.button("🪄 AI 智能生成中文文案"):
        st.session_state['zh_temp'] = call_deepseek(en_desc)
    zh_desc = st.text_area("中文文案确认", value=st.session_state.get('zh_temp', ''))

    st.subheader("2. 批量上传照片 (最多6张生成海报)")
    uploaded_files = st.file_uploader("选择房源图片", accept_multiple_files=True, type=['jpg','png'])
    
    if uploaded_files and st.button("🎨 生成六图带水印海报"):
        final_poster = create_multi_photo_poster(uploaded_files, new_title, new_price)
        st.image(final_poster, caption="预览生成的海报")
        buf = BytesIO()
        final_poster.save(buf, format="JPEG")
        st.download_button("📥 下载海报", buf.getvalue(), "poster.jpg")

with tab_manage:
    st.subheader("📊 房源库维护")
    # 找回编辑、删除、精选功能
    for i, row in df.iterrows():
        with st.expander(f"{'⭐' if row['is_featured'] else ''} {row['title']} - £{row['price']}"):
            col_e1, col_e2, col_e3 = st.columns(3)
            
            # 精选切换
            if col_e1.button(f"{'取消' if row['is_featured'] else '设为'}精选", key=f"feat_{i}"):
                new_val = 0 if row['is_featured'] else 1
                ws.update_cell(i + 2, df.columns.get_loc("is_featured") + 1, new_val)
                st.rerun()
            
            # 删除功能
            if col_e2.button("🗑️ 删除房源", key=f"del_{i}"):
                ws.delete_rows(i + 2)
                st.success("已删除")
                st.rerun()
            
            # 简单编辑演示（价格修改）
            new_p = col_e3.number_input("修改租金", value=int(row['price']), key=f"edit_p_{i}")
            if col_e3.button("保存修改", key=f"save_{i}"):
                ws.update_cell(i + 2, df.columns.get_loc("price") + 1, new_p)
                st.success("价格已更新")
