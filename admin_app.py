import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
import requests
from io import BytesIO

# 页面配置
st.set_page_config(page_title="Hao Harbour 房源管理", layout="wide")
st.title("🏡 Hao Harbour 数据与 AI 管理系统")

# --- 1. 稳定连接 Google Sheets ---
def connect_to_gsheets():
    try:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped)
        # 使用 URL 强制连接防止 404
        sheet_url = "https://docs.google.com/spreadsheets/d/1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74/edit#gid=0"
        return gc.open_by_url(sheet_url).get_worksheet(0)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# --- 2. DeepSeek AI 提取功能 ---
def deepseek_extract(text):
    try:
        # 使用 DeepSeek 配置
        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            base_url=st.secrets["OPENAI_BASE_URL"]
        )
        response = client.chat.completions.create(
            model="deepseek-chat", # 或者 deepseek-reasoner
            messages=[
                {"role": "system", "content": "你是一个伦敦房产专家，请从描述中提取：租金(月/周)、户型、邮编、起租时间。用简洁的列表回复。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek 分析出错: {e}"

# --- 主程序 ---
worksheet = connect_to_gsheets()

if worksheet:
    # 获取数据并清洗列名
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    tab1, tab2, tab3 = st.tabs(["📊 数据总览", "🤖 AI 提取分析", "🎨 海报预览"])

    with tab1:
        st.subheader("在线房源看板")
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("DeepSeek 智能解析")
        if 'title' in df.columns:
            selected_title = st.selectbox("选择要分析的房源", df['title'].tolist())
            desc_text = df[df['title'] == selected_title]['description'].values[0]
            
            col_a, col_b = st.columns(2)
            col_a.info("原始描述:")
            col_a.write(desc_text)
            
            if col_b.button("🚀 调用 DeepSeek 提取信息"):
                with st.spinner("DeepSeek 思考中..."):
                    res = deepseek_extract(desc_text)
                    col_b.success("分析结果:")
                    col_b.markdown(res)

    with tab3:
        st.subheader("海报与托管信息")
        if 'poster_link' in df.columns:
            selected_house = st.selectbox("预览海报房源", df['title'].tolist())
            row = df[df['title'] == selected_house].iloc[0]
            
            img_url = row['poster_link']
            if img_url:
                st.image(img_url, caption=f"海报链接: {img_url}", use_container_width=True)
                st.write(f"Cloudinary 存储账户: {st.secrets['CLOUDINARY_CLOUD_NAME']}")
            else:
                st.warning("该房源暂无海报链接")

else:
    st.error("无法加载数据，请检查 Secrets 配置。")
