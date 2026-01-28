import streamlit as st
import pandas as pd
import io, requests, cloudinary
import cloudinary.uploader
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. 初始化配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 认证
cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 核心连接函数 ---
def get_gs_conn():
    """使用上一版验证通过的稳健连接逻辑"""
    try:
        fixed_key = st.secrets["GS_PRIVATE_KEY"].replace("\\n", "\n")
        creds = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": fixed_key,
            "client_email": st.secrets["GS_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        return st.connection("gsheets", type=GSheetsConnection, **creds)
    except Exception as e:
        st.error(f"连接初始化失败: {e}")
        return None

def call_ai_logic(text):
    """AI 提取房源要点逻辑"""
    try:
        headers = {"Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except:
        return "AI 提取失败，请手动输入。"

# --- 3. UI 界面布局 ---
tab1, tab2 = st.tabs(["🚀 发布房源", "📊 管理中心"])

# --- TAB 1: 发布房源 ---
with tab1:
    st.subheader("🆕 发布新房源")
    
    # 状态管理：保存 AI 提取的内容
    if "ai_result" not in st.session_state:
        st.session_state.ai_result = ""

    col_left, col_right = st.columns(2)
    
    with col_left:
        n_title = st.text_input("房源名称 (例如: River Park Tower)")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述 (用于 AI 提取)", height=200)
        if st.button("✨ AI 提取要点"):
            if n_raw:
                with st.spinner("AI 正在分析..."):
                    st.session_state.ai_result = call_ai_logic(n_raw)
            else:
                st.warning("请先粘贴英文描述")

    with col_right:
        n_desc = st.text_area("最终描述 (发给客户看的内容)", value=st.session_state.ai_result, height=335)
        n_pics = st.file_uploader("上传图片", accept_multiple_files=True)

    if st.button("📤 确认发布房源", type="primary", use_container_width=True):
        if not n_title or not n_pics:
            st.error("房源名称和图片是必填项！")
        else:
            try:
                with st.spinner("正在发布中..."):
                    # 1. 上传图片到 Cloudinary
                    img_url = cloudinary.uploader.upload(n_pics[0])['secure_url']
                    
                    # 2. 连接 Google Sheets
                    conn = get_gs_conn()
                    df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
                    
                    # 3. 构造新行数据
                    new_row = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "title": n_title,
                        "region": n_reg,
                        "price": n_price,
                        "poster-link": img_url,
                        "description": n_desc
                    }])
                    
                    # 4. 更新表格
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=updated_df)
                    
                    st.success(f"✅ {n_title} 已成功发布！")
                    st.session_state.ai_result = "" # 清空 AI 缓存
            except Exception as e:
                st.error(f"发布过程出错: {e}")

# --- TAB 2: 管理中心 ---
with tab2:
    st.subheader("📋 现有房源管理")
    if st.button("🔄 刷新表格数据"):
        try:
            conn = get_gs_conn()
            # 明确指定 spreadsheet URL
            df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                st.divider()
                # 删除功能
                del_title = st.selectbox("选择要下架的房源", df['title'].tolist())
                if st.button("🗑️ 确认下架该房源"):
                    new_df = df[df['title'] != del_title]
                    conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=new_df)
                    st.warning(f"房源 {del_title} 已删除")
                    st.rerun()
            else:
                st.info("目前表格中没有数据。")
        except Exception as e:
            st.error(f"数据加载失败: {e}")
