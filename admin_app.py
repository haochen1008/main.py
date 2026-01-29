import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import requests

st.set_page_config(page_title="Hao Harbour 房源智能管理", layout="wide")

# --- 1. 核心连接 (已验证的稳定版) ---
def get_worksheet():
    try:
        info = dict(st.secrets["gcp_service_account"])
        key_parts = ["MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCRayoKdXw38HlF", "6J23Bbyq7zAzCWQ5OAtzk0/fOhbnFUHJTMOF1njbBw92x9etYoDt5WbBUwbexaQE", "6mTmvNU0pIGEH+iUWxvkb0VNWe3o1AceLLyDECR8p+srO04Un9hP9N0k+3SzNUFo", "xTSQCMg+GVDLJN2TLTZ3MaAuJY+UtZ+tk0K01PMZGRGu8Jl0iSZhlsbZeTSptzMJ", "UIZRnbIu8HVGVfZYGWEb1sWmUBMKsJAkr5nWPDCTgQex98rdrgSKNxT+I8x6nQMz", "pkqVTcAOlShz8bXr85C/g+t8wFMSFZKi0KGdweZY1pgTkRe7589V/ne4omfK0oqu", "q7BLqPYtAgMBAAECgf9yRxG3eT+Az4zYsAWlrSuOeY9l/67YwQF2CB/3nDAprTQ+", "QAxnf2HIUA4mEdTysdwMO1ptOvuiY8DOZ2paAtvzjg2ypW/PqSQd4e9R25K4PxT5", "h0UvZO1bpLOOCFwWgVAcEjKZ1MEmIzonCN0Kx22aqtRmJblpc4uwgcZ53MHmN1qH", "UoSB1zw9c6EEoevxDAlve7yuVE5BU0kHtyaQANTShDjbLMFt2yvRBY4ZSuqJVjKG", "BWt6gTPyTHm3JcMxNOkEaxT/4eJytU1GUuqxShQf4rRCfeaCCcBPnzWl9LigYQ1O", "+s3b6rxjioi2p+nzgzhVpQVnaa7eGxojoaNpkukCgYEAwytmFQ1oLK+EzET6u2Bt", "O/qB2sxn3iKFaHMRBF2HEAOmmwCxqipvswiQmrV2pX1t+TQd+kk5z6iEpgsmm9HY", "mdUv9QBN23TmOfS1UJjLkeKmRfanhr700QpwW29yuL/RBpvSanXDnreiFw5gMT+/", "/AODyVyKDzPUwleamZtsvrUCgYEAvr4iMO8B9u6j4EPVa8XKl2ho2tm9qgrviIbd", "dvu4itmgECC/BWEsvJhgoqm1jG8A+KMhf5oUZJKrwMB0EjOM+r43PzjYfY+CvtAz", "Mfea+rbhCWootwt9YWeqkBay00jtVe0kKMcaXzfcNUucDRDa8+8RLhUunBx6SzGj", "BW3gjJkCgYB4ZpeNOT4hAw6brZo4ah45OCtPvXX+VbGTZBkFZmVh/b6UNPNllNRf", "0FLU/kl5gk2LxRkRRIdDkiRzAsIIsoY7MIdrT4q4bf9xlYMde4VqNDZ7RtTGjZse", "MqBp5/EQBFWBDDPctVW+3m5CZv30o+1eHRT57frFsiX41m5rgLSvWQKBgDvGZfyj", "yh/SZXTQjT96+qQ8Si/bcL6rMqm8agbxl8GbtbeYK4TKETUBI7eWK5jY6JsCtGrC", "pIVoGX8MUNOraBDkL3gWnnGq2bRmlsSf7eeIDDnhFOVYKnCuBhuloWDpR8dXy68j", "xjX00YO6MCtADv3G+8FPTg4KNqD96zK2XlpxAoGAWxLPxsJM71wnUXloar4X1pZU", "H5sKI9x0ivkug/DwaDbXZP4CO5f09L1yvQhXN1hQVqBKENXFOKgT1ZkKc5aIo+Py", "8GkcvwcQLsXUrli1JW0dbTUYYFH+lbvB7Kpn78Lxgdwv0vYFbTjAeW1Pgyzq9G97", "6FI0qUia8eWEUNibK1k="]
        info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_parts) + "\n-----END PRIVATE KEY-----"
        creds = service_account.Credentials.from_service_account_info(info)
        gc = gspread.authorize(creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
        return gc.open("Hao_Harbour_DB").get_worksheet(0)
    except: return None

# --- 2. 界面切换 ---
tab1, tab2 = st.tabs(["✨ 发布与海报生成", "🗄️ 房源库管理"])

# --- Tab 1: 发布与海报 ---
with tab1:
    st.subheader("📝 录入新房源")
    with st.form("main_form"):
        c1, c2, c3 = st.columns(3)
        title = c1.text_input("房源名称")
        region = c2.selectbox("区域", ["东伦敦", "西伦敦", "南伦敦", "北伦敦", "中伦敦"])
        rooms = c3.selectbox("户型", ["Studio", "1房", "2房", "3房+"])
        
        price = st.number_input("月租 (£)", min_value=0)
        en_desc = st.text_area("粘贴英文描述 (English Description)", height=150)
        
        uploaded_files = st.file_uploader("添加房源照片 (最多6张)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("🚀 AI 提取并生成海报")

    if submit:
        # AI 提取总结
        with st.spinner("DeepSeek 正在解析并总结..."):
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
            ai_res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "你是一个伦敦房产专家。请把这段英文描述总结成简洁的中文要点，包含租金、户型、交通和亮点。"},
                          {"role": "user", "content": en_desc}]
            )
            zh_summary = ai_res.choices[0].message.content
        
        st.success("✅ AI 中文总结已生成")
        st.info(zh_summary)

        # 展示照片
        if uploaded_files:
            st.write("📷 已添加的照片预览:")
            cols = st.columns(3)
            for idx, file in enumerate(uploaded_files[:6]):
                cols[idx % 3].image(file, use_container_width=True)

        # 生成海报 (Canvas 模拟)
        st.divider()
        st.subheader("🎨 预览生成的海报")
        poster_bg = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(poster_bg)
        # 这里简单展示海报文字预览，实际可用 ImageFont 渲染
        draw.text((50, 50), f"Hao Harbour: {title}", fill=(0,0,0))
        draw.text((50, 100), f"Region: {region} | Price: £{price}", fill=(50,50,50))
        
        st.image(poster_bg, caption="点击右键保存海报")
        
        # 写入数据库
        ws = get_worksheet()
        if ws:
            ws.append_row([str(datetime.now().date()), title, region, rooms, price, "", zh_summary, 0])
            st.balloons()

# --- Tab 2: 房源管理 ---
with tab2:
    st.subheader("📊 房源库管理")
    ws = get_worksheet()
    if ws:
        df = pd.DataFrame(ws.get_all_records())
        
        # 搜索
        search = st.text_input("🔍 搜索名称")
        if search:
            df = df[df['title'].str.contains(search, case=False)]
        
        # 渲染列表，带 Feature 切换和删除
        for index, row in df.iterrows():
            with st.expander(f"{'⭐' if row.get('is_featured') == 1 else ''} {row['title']} - {row['region']}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**价格:** £{row['price']} | **户型:** {row['rooms']}")
                col1.write(f"**总结:** {row['description']}")
                
                # Feature 功能
                if col2.button("设为精选", key=f"feat_{index}"):
                    ws.update_cell(index + 2, 8, 1) # 假设第8列是 is_featured
                    st.rerun()
                
                # 删除功能
                if col3.button("🗑️ 删除", key=f"del_{index}"):
                    ws.delete_rows(index + 2)
                    st.warning(f"已删除 {row['title']}")
                    st.rerun()

    else:
        st.error("数据加载失败。")
