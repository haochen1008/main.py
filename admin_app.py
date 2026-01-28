import streamlit as st
import pandas as pd
import io, requests, cloudinary
import cloudinary.uploader
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. 初始化 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# Cloudinary 认证
cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

# --- 2. 核心连接函数 ---
def get_gs_conn():
    """手动构建凭据，彻底避开参数冲突"""
    try:
        # 修正密钥格式问题
        fixed_key = st.secrets["GS_PRIVATE_KEY"].replace("\\n", "\n")
        creds = {
            "type": "service_account",
            "project_id": "canvas-voltage-278814",
            "private_key": fixed_key,
            "client_email": st.secrets["GS_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        # 不传 type=GSheetsConnection 以避免 Multiple values 报错
        return st.connection("gsheets", **creds)
    except Exception as e:
        st.error(f"连接初始化失败: {e}")
        return None

def call_ai_logic(text):
    """提取房源要点"""
    try:
        headers = {"Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers,
                            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                            timeout=15)
        return res.json()['choices'][0]['message']['content']
    except:
        return "AI 提取失败，请手动录入。"

# --- 3. UI 界面 ---
tab1, tab2 = st.tabs(["🚀 发布新房源", "📋 房源管理中心"])

with tab1:
    st.subheader("🆕 录入新房源信息")
    if "ai_note" not in st.session_state: st.session_state.ai_note = ""

    col1, col2 = st.columns(2)
    with col1:
        n_title = st.text_input("房源名称 (Title)")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("英文描述 (用于 AI 提取)", height=200)
        if st.button("✨ 执行 AI 提取"):
            if n_raw:
                st.session_state.ai_note = call_ai_logic(n_raw)
            else:
                st.warning("请先输入内容")

    with col2:
        n_desc = st.text_area("最终文案 (展示给客户)", value=st.session_state.ai_note, height=335)
        n_pics = st.file_uploader("上传房源封面图", type=['jpg', 'png', 'jpeg'])

    if st.button("📤 确认并发布到表格", type="primary", use_container_width=True):
        if not n_title or not n_pics:
            st.error("名称和图片是必填的！")
        else:
            try:
                with st.spinner("正在同步数据..."):
                    img_url = cloudinary.uploader.upload(n_pics)['secure_url']
                    conn = get_gs_conn()
                    # 必须在此明确传 URL，避开 connection 构造时的 bug
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
                    st.success(f"✅ {n_title} 发布成功！")
                    st.session_state.ai_note = "" 
            except Exception as e:
                st.error(f"发布失败: {e}")

with tab2:
    st.subheader("📊 现有房源数据")
    if st.button("🔄 刷新房源看板"):
        try:
            conn = get_gs_conn()
            df = conn.read(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", ttl=0).dropna(how='all')
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.divider()
                # 简单的删除逻辑
                target = st.selectbox("下架房源", df['title'].tolist())
                if st.button("🗑️ 确认下架"):
                    df = df[df['title'] != target]
                    conn.update(spreadsheet=st.secrets["GS_URL"], worksheet="Sheet1", data=df)
                    st.warning(f"已下架: {target}")
                    st.rerun()
            else:
                st.info("表格里空空如也，快去发布吧！")
        except Exception as e:
            st.error(f"加载数据失败: {e}")
