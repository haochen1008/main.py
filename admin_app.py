import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 认证
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )
except:
    st.error("Cloudinary 配置缺失，请检查 Secrets")

DEEPSEEK_KEY = st.secrets.get("OPENAI_API_KEY", "")

# --- 2. 核心工具函数 ---

def get_gsheets_conn():
    """
    终极连接函数：解决 PEM 加载错误及参数冲突问题。
    """
    # 1. 获取 Secrets 副本
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    
    # 2. 核心修复：处理私钥换行符 (解决 Unable to load PEM file)
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    # 3. 核心修复：移除冲突参数 (解决 multiple values for keyword argument 'type')
    # 因为 st.connection 第一个参数是连接名称，第二个参数是类，
    # 如果 creds_dict 里还有 type 字段，会导致冲突。
    if "type" in creds_dict:
        del creds_dict["type"]
    
    # 4. 建立连接
    return st.connection("gsheets", type=GSheetsConnection, **creds_dict)

def call_ai_logic(text):
    """调用 AI 提取房源要点"""
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败: {str(e)}"

def create_poster(files, title_text):
    """生成预览海报"""
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try: 
            font_t = ImageFont.truetype("simhei.ttf", 45)
            font_f = ImageFont.truetype("simhei.ttf", 25)
        except: 
            font_t = font_f = ImageFont.load_default()
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        draw.text((40, 950), title_text, font=font_t, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_f, fill=(180, 160, 100))
        return canvas
    except: 
        return None

# --- 3. UI 界面布局 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

# --- TAB 1: 发布房源逻辑 ---
with tab1:
    st.subheader("🚀 发布新房源")
    if "new_ai_desc" not in st.session_state:
        st.session_state.new_ai_desc = ""
        
    col_a, col_b = st.columns(2)
    with col_a:
        n_title = st.text_input("房源名称 (例如: River Park Tower)")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述", height=150)
        if st.button("✨ 执行 AI 提取", key="btn_new_ai"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            st.rerun()
            
    with col_b:
        n_desc = st.text_area("编辑 AI 提取结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传房源图片", accept_multiple_files=True)
        if st.button("📤 确认发布并生成海报", type="primary"):
            if not n_pics:
                st.error("请先上传图片！")
            else:
                try:
                    with st.spinner("正在处理并上传..."):
                        poster = create_poster(n_pics, n_title)
                        buf = io.BytesIO()
                        poster.save(buf, format='JPEG')
                        url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                        
                        conn = get_gsheets_conn()
                        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                        
                        new_row = {
                            "date": datetime.now().strftime("%Y-%m-%d"), 
                            "title": n_title, "region": n_reg, "rooms": n_room, 
                            "price": n_price, "poster-link": url, "description": n_desc,
                            "views": 0, "is_featured": False
                        }
                        
                        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("房源发布成功！")
                        st.session_state.new_ai_desc = ""
                        st.rerun()
                except Exception as e:
                    st.error(f"发布失败: {e}")

# --- TAB 2: 管理中心逻辑 ---
with tab2:
    st.subheader("📊 房源看板与快速管理")
    try:
        conn = get_gsheets_conn()
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.write("---")
            delete_title = st.selectbox("选择要下架的房源", df['title'].tolist())
            if st.button("🗑️ 确认下架"):
                df = df[df['title'] != delete_title]
                conn.update(worksheet="Sheet1", data=df)
                st.warning(f"房源 '{delete_title}' 已下架")
                st.rerun()
        else:
            st.info("暂无房源数据。")
    except Exception as e:
        st.error(f"管理中心连接失败: {e}")
