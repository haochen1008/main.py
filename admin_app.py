import streamlit as st
import pandas as pd
import io, requests, cloudinary
import cloudinary.uploader
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. 配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 修正后的核心函数 ---
def get_gs_conn():
    """手动构建凭据字典，避开 Secrets 自动加载的冲突"""
    try:
        # 必须确保这里的缩进是 4 个空格
        fixed_key = st.secrets["GS_PRIVATE_KEY"].replace("\\n", "\n")
        creds = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": fixed_key,
            "client_email": st.secrets["GS_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        # 不传 type=GSheetsConnection 避开 Multiple values 报错
        return st.connection("gsheets", **creds)
    except Exception as e:
        st.error(f"连接初始化失败: {e}")
        return None

def call_ai_logic(text):
    """AI 提取房源要点"""
    try:
        headers = {"Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"}
        prompt = f"精简翻译成中文要点，包含Available date，✔开头：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except:
        return "AI 提取失败，请手动输入。"

# --- 3. UI 界面 ---
tab1, tab2 = st.tabs(["🚀 发布新房源", "📊 管理中心"])

with tab1:
    st.subheader("录入信息")
    if "ai_note" not in st.session_state: st.session_state.ai_note = ""
    
    col1, col2 = st.columns(2)
    with col1:
        n_title = st.text_input("房源名称")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文描述", height=150)
        if st.button("✨ AI 提取"):
            st.session_state.ai_note = call_ai_logic(n_raw)
            st.rerun()

    with col2:
        n_desc = st.text_area("最终文案", value=st.session_state.ai_note, height=275)
        n_pics = st.file_uploader("上传封面图", type=['jpg', 'png', 'jpeg'])

    if st.button("📤 确认发布", type="primary", use_container_width=True):
        if n_title and n_pics:
            try:
                with st.spinner("发布中..."):
                    img_url = cloudinary.uploader.upload(n_pics)['secure_url']
                    conn = get_gs_conn()
                    df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
                    
                    new_row = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "title": n_title,
                        "region": n_reg,
                        "price": n_price,
                        "poster-link": img_url,
                        "description": n_desc
                    }])
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=updated_df)
                    st.success("发布成功！")
            except Exception as e:
                st.error(f"发布失败: {e}")

with tab2:
    st.subheader("现有房源")
    if st.button("🔄 刷新看板"):
        try:
            conn = get_gs_conn()
            df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"加载失败: {e}")
