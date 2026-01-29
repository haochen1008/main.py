import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
import requests

st.title("🏡 Hao Harbour 数据与 AI 管理系统")

# 1. 获取客户端 (无缓存模式，确保每次都是最新认证)
def get_client():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # 严格处理换行符
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").replace('\\\\n', '\n').strip()
        
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"❌ 认证配置解析失败: {e}")
        return None

client = get_client()

if client:
    # 尝试通过 URL 访问表格
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74/edit#gid=0"
    
    try:
        sh = client.open_by_url(SHEET_URL)
        worksheet = sh.get_worksheet(0)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        st.success("🎉 连接成功！数据已实时同步。")
        
        tab1, tab2, tab3 = st.tabs(["📊 实时看板", "🤖 AI 提取", "🎨 海报预览"])
        
        with tab1:
            st.dataframe(df, use_container_width=True)
            
        with tab2:
            st.subheader("DeepSeek 智能解析")
            selected = st.selectbox("选择分析房源", df['title'].tolist())
            desc = df[df['title'] == selected]['description'].values[0]
            if st.button("🚀 开始分析"):
                ai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
                res = ai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": f"提取房源要点: {desc}"}]
                )
                st.write(res.choices[0].message.content)

        with tab3:
            st.subheader("海报管理")
            selected_img = st.selectbox("预览海报", df['title'].tolist())
            img_url = df[df['title'] == selected_img]['poster_link'].values[0]
            if img_url:
                st.image(img_url, use_container_width=True)
                
    except Exception as e:
        st.error(f"❌ 依然无法访问表格: {e}")
        st.info("提示：请确认 Drive API 启用后已等待 2 分钟，且分享邮箱拼写无误。")
