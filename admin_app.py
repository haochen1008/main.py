import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
import requests

st.set_page_config(page_title="Hao Harbour 综合管理", layout="wide")
st.title("🏡 Hao Harbour 数据与 AI 管理系统")

# --- 1. 终极加固版连接逻辑 ---
@st.cache_resource
def get_gsheet_client():
    try:
        # 获取并彻底清洗私钥
        creds_info = dict(st.secrets["gcp_service_account"])
        # 针对不同系统环境处理换行符，防止 InvalidByte 报错
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n").strip()
        
        creds = service_account.Credentials.from_service_account_info(creds_info)
        scoped = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"认证解析失败: {e}")
        return None

def get_worksheet():
    client = get_gsheet_client()
    if client:
        try:
            # 你的表格 URL
            url = "https://docs.google.com/spreadsheets/d/1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74/edit#gid=0"
            sh = client.open_by_url(url)
            return sh.get_worksheet(0)
        except Exception as e:
            st.error(f"连接失败: <Response [404]> - 无法访问表格文件")
            st.info("请检查 Google Cloud 是否开启了 'Google Drive API'")
            return None
    return None

# --- 2. DeepSeek AI 提取功能 ---
def deepseek_analyze(text):
    try:
        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            base_url=st.secrets["OPENAI_BASE_URL"]
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个房产分析专家，请从描述中提取租金、户型、邮编和起租日期。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 分析出错: {e}"

# --- 主界面逻辑 ---
worksheet = get_worksheet()

if worksheet:
    # 成功获取数据
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    # 导航栏
    tab1, tab2, tab3 = st.tabs(["📊 实时看板", "🤖 AI 智能解析", "🖼️ 海报与托管"])

    with tab1:
        st.subheader("当前房源明细")
        st.dataframe(df, use_container_width=True)
        st.success("✅ 数据拉取成功！")

    with tab2:
        st.subheader("DeepSeek 房源要点提取")
        if not df.empty and 'title' in df.columns:
            selected = st.selectbox("选择房源进行分析", df['title'].tolist())
            row_data = df[df['title'] == selected].iloc[0]
            desc = row_data.get('description', '无描述')
            
            st.text_area("房源描述文本", desc, height=100)
            if st.button("🚀 开始 AI 分析"):
                with st.spinner("DeepSeek 正在解析..."):
                    result = deepseek_analyze(desc)
                    st.markdown("---")
                    st.markdown(result)
        else:
            st.warning("表格中未找到房源数据或 'title' 列")

    with tab3:
        st.subheader("Cloudinary 图片托管状态")
        if not df.empty and 'poster_link' in df.columns:
            selected_img = st.selectbox("预览海报", df['title'].tolist())
            img_url = df[df['title'] == selected_img]['poster_link'].values[0]
            
            if img_url and str(img_url).startswith("http"):
                st.image(img_url, use_container_width=True)
                st.code(f"托管地址: {img_url}")
            else:
                st.warning("该房源暂无海报链接")
        
        # 展示 API 状态
        st.divider()
        st.write(f"**Cloudinary Cloud:** `{st.secrets['CLOUDINARY_CLOUD_NAME']}`")
        st.write(f"**ImgBB Status:** Active")
