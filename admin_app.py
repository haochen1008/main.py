import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import time

# --- 1. 数据库连接 (使用您 secrets 中的配置) ---
def get_gs_worksheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(creds)
        # 确保表格名称正确
        return gc.open("Hao_Harbour_DB").get_worksheet(0)
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None

# --- 2. DeepSeek 智能文案提取逻辑 ---
def ai_extract_chinese(english_text):
    if not english_text:
        return "请先在上方粘贴英文描述"
    
    try:
        api_key = st.secrets["OPENAI_API_KEY"] # 确保 secrets 中已填入 DeepSeek Key
        # DeepSeek 官方 API 端点
        base_url = "https://api.deepseek.com/chat/completions"
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个伦敦豪宅中介，请将英文描述总结为专业的中文卖点，包含租金、户型、地理优势，使用列表格式。"},
                {"role": "user", "content": english_text}
            ],
            "temperature": 0.7
        }
        response = requests.post(base_url, json=payload, headers=headers, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"DeepSeek 提取失败: {str(e)}"

# --- 3. 海报生成引擎 (带 45° 倾斜全屏水印) ---
def generate_poster_with_watermark(img_file, title, price, region):
    try:
        # A. 读取并缩放底图 (1080x1440 黄金比例)
        base_img = Image.open(img_file).convert("RGBA").resize((1080, 1440))
        
        # B. 创建一个巨大的水印层（为了旋转时不露白边）
        watermark_layer = Image.new("RGBA", (2000, 2000), (0, 0, 0, 0))
        draw_wm = ImageDraw.Draw(watermark_layer)
        
        # C. 填充重复的水印文字
        wm_text = "HAO HARBOUR EXCLUSIVE    " * 4
        for y in range(0, 2000, 250): # 垂直间距
            draw_wm.text((0, y), wm_text, fill=(255, 255, 255, 45)) # 45 为透明度
        
        # D. 旋转 45 度并粘贴回底图中心
        watermark_layer = watermark_layer.rotate(45, expand=False)
        # 计算偏移使其居中
        base_img.paste(watermark_layer, (-450, -450), watermark_layer)
        
        # E. 叠加底部黑色半透明信息栏
        info_overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        draw_info = ImageDraw.Draw(info_overlay)
        draw_info.rectangle([0, 1150, 1080, 1440], fill=(26, 28, 35, 220)) # 底座
        
        # F. 写入文本信息 (金色标题 + 白色详情)
        draw_info.text((60, 1200), f"PROPERTY: {title}", fill=(191, 160, 100, 255))
        draw_info.text((60, 1300), f"PRICE: £{price} /month | {region}", fill=(255, 255, 255, 255))
        
        # 合成最终图像
        final_poster = Image.alpha_composite(base_img, info_overlay)
        return final_poster.convert("RGB")
    except Exception as e:
        st.error(f"海报生成失败: {e}")
        return None

# --- 4. 管理后台界面 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
st.title("🛡️ 房源管理后台 (DeepSeek 增强版)")

t1, t2 = st.tabs(["✨ 智能发布海报", "🗄️ 房源库预览"])

with t1:
    st.header("1. 基础信息录入")
    # 修复了 Form 导致的交互问题，采用 Session State 保持状态
    col1, col2, col3 = st.columns(3)
    p_name = col1.text_input("房源名称", placeholder="例如: Triptych Bankside")
    p_region = col2.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "北伦敦", "南伦敦"])
    p_price = col3.number_input("租金 (£/月)", min_value=0, step=100)
    
    p_rooms = st.selectbox("户型选择", ["Studio", "1房", "2房", "3房", "4房+"]) # 完整户型
    
    en_desc = st.text_area("粘贴英文描述", height=150, help="粘贴 Rightmove/Zoopla 的英文描述")
    
    # 智能提取按钮 (DeepSeek 驱动)
    if st.button("🪄 智能提取中文文案 (DeepSeek)"):
        with st.spinner("DeepSeek AI 正在生成中..."):
            st.session_state['zh_content'] = ai_extract_chinese(en_desc)
    
    final_zh = st.text_area("编辑并确认中文文案", value=st.session_state.get('zh_content', ''), height=180)
    
    st.write("---")
    st.header("2. 海报合成 (45° 防伪水印)")
    uploaded_img = st.file_uploader("上传房源主图", type=["jpg", "png", "jpeg"])
    
    if uploaded_img:
        if st.button("🎨 点击合成预览海报"):
            poster_res = generate_poster_with_watermark(uploaded_img, p_name, p_price, p_region)
            if poster_res:
                st.image(poster_res, caption="合成海报预览 (45度倾斜防伪水印)")
                buf = BytesIO()
                poster_res.save(buf, format="JPEG", quality=95)
                st.download_button("📥 下载此海报至电脑", buf.getvalue(), f"Poster_{p_name}.jpg", "image/jpeg")

with t2:
    st.header("房源库实时数据")
    ws = get_gs_worksheet()
    if ws:
        data = pd.DataFrame(ws.get_all_records())
        st.dataframe(data, use_container_width=True)
