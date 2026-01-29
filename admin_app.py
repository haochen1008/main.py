import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO

# 页面配置
st.set_page_config(page_title="Hao Harbour 综合管理系统", layout="wide")
st.title("🏡 Hao Harbour 数据与 AI 管理中心")

# --- 1. 底层连接逻辑 (已验证成功) ---
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
        sheet_url = "https://docs.google.com/spreadsheets/d/1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74/edit#gid=0"
        return gc.open_by_url(sheet_url).get_worksheet(0)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# --- 2. AI 提取逻辑 ---
def ai_extract_info(description):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个房产专家，请从描述中提取：租金、户型、地理位置、核心卖点。用简洁的列表回复。"},
                {"role": "user", "content": description}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 提取出错: {e}"

# --- 主程序逻辑 ---
worksheet = connect_to_gsheets()

if worksheet:
    # 侧边栏功能
    menu = st.sidebar.selectbox("选择功能", ["📊 房源看板", "🤖 AI 描述分析", "🎨 海报预览"])
    
    # 获取数据
    raw_data = worksheet.get_all_records()
    df = pd.DataFrame(raw_data)

    if menu == "📊 房源看板":
        st.subheader("当前在线房源")
        st.dataframe(df, use_container_width=True)
        st.info(f"共监测到 {len(df)} 套房源")

    elif menu == "🤖 AI 描述分析":
        st.subheader("智能提取房源要点")
        target_row = st.selectbox("选择要分析的房源", df['title'].tolist())
        desc = df[df['title'] == target_row]['description'].values[0]
        
        st.text_area("原始描述", desc, height=150)
        if st.button("开始 AI 分析"):
            with st.spinner("AI 正在深度解析..."):
                result = ai_extract_info(desc)
                st.markdown("### 📌 AI 提取结果")
                st.write(result)

    elif menu == "🎨 海报预览":
        st.subheader("社交媒体海报生成预览")
        col1, col2 = st.columns([1, 2])
        
        selected_house = col1.selectbox("选择海报房源", df['title'].tolist())
        house_info = df[df['title'] == selected_house].iloc[0]
        
        with col2:
            st.write(f"**房源名称:** {house_info['title']}")
            st.write(f"**价格:** £{house_info['price']}/月")
            
            # 尝试加载图片
            try:
                img_url = house_info['poster_link']
                response = requests.get(img_url)
                img = Image.open(BytesIO(response.content))
                st.image(img, caption=f"海报预览: {selected_house}", use_container_width=True)
                
                # 下载按钮
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.download_button(label="💾 下载海报图片", data=buf.getvalue(), file_name=f"{selected_house}.png", mime="image/png")
            except:
                st.warning("该房源暂无有效海报链接")

else:
    st.error("数据源未就绪，请检查 Secrets 配置。")
