import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
from datetime import datetime

st.set_page_config(page_title="Hao Harbour 房源发布系统", layout="wide")

# --- 1. 核心连接逻辑 ---
def get_worksheet():
    try:
        info = dict(st.secrets["gcp_service_account"])
        # 物理拼装私钥，确保格式绝对正确
        key_parts = [
            "MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCRayoKdXw38HlF",
            "6J23Bbyq7zAzCWQ5OAtzk0/fOhbnFUHJTMOF1njbBw92x9etYoDt5WbBUwbexaQE",
            "6mTmvNU0pIGEH+iUWxvkb0VNWe3o1AceLLyDECR8p+srO04Un9hP9N0k+3SzNUFo",
            "xTSQCMg+GVDLJN2TLTZ3MaAuJY+UtZ+tk0K01PMZGRGu8Jl0iSZhlsbZeTSptzMJ",
            "UIZRnbIu8HVGVfZYGWEb1sWmUBMKsJAkr5nWPDCTgQex98rdrgSKNxT+I8x6nQMz",
            "pkqVTcAOlShz8bXr85C/g+t8wFMSFZKi0KGdweZY1pgTkRe7589V/ne4omfK0oqu",
            "q7BLqPYtAgMBAAECgf9yRxG3eT+Az4zYsAWlrSuOeY9l/67YwQF2CB/3nDAprTQ+",
            "QAxnf2HIUA4mEdTysdwMO1ptOvuiY8DOZ2paAtvzjg2ypW/PqSQd4e9R25K4PxT5",
            "h0UvZO1bpLOOCFwWgVAcEjKZ1MEmIzonCN0Kx22aqtRmJblpc4uwgcZ53MHmN1qH",
            "UoSB1zw9c6EEoevxDAlve7yuVE5BU0kHtyaQANTShDjbLMFt2yvRBY4ZSuqJVjKG",
            "BWt6gTPyTHm3JcMxNOkEaxT/4eJytU1GUuqxShQf4rRCfeaCCcBPnzWl9LigYQ1O",
            "+s3b6rxjioi2p+nzgzhVpQVnaa7eGxojoaNpkukCgYEAwytmFQ1oLK+EzET6u2Bt",
            "O/qB2sxn3iKFaHMRBF2HEAOmmwCxqipvswiQmrV2pX1t+TQd+kk5z6iEpgsmm9HY",
            "mdUv9QBN23TmOfS1UJjLkeKmRfanhr700QpwW29yuL/RBpvSanXDnreiFw5gMT+/",
            "/AODyVyKDzPUwleamZtsvrUCgYEAvr4iMO8B9u6j4EPVa8XKl2ho2tm9qgrviIbd",
            "dvu4itmgECC/BWEsvJhgoqm1jG8A+KMhf5oUZJKrwMB0EjOM+r43PzjYfY+CvtAz",
            "Mfea+rbhCWootwt9YWeqkBay00jtVe0kKMcaXzfcNUucDRDa8+8RLhUunBx6SzGj",
            "BW3gjJkCgYB4ZpeNOT4hAw6brZo4ah45OCtPvXX+VbGTZBkFZmVh/b6UNPNllNRf",
            "0FLU/kl5gk2LxRkRRIdDkiRzAsIIsoY7MIdrT4q4bf9xlYMde4VqNDZ7RtTGjZse",
            "MqBp5/EQBFWBDDPctVW+3m5CZv30o+1eHRT57frFsiX41m5rgLSvWQKBgDvGZfyj",
            "yh/SZXTQjT96+qQ8Si/bcL6rMqm8agbxl8GbtbeYK4TKETUBI7eWK5jY6JsCtGrC",
            "pIVoGX8MUNOraBDkL3gWnnGq2bRmlsSf7eeIDDnhFOVYKnCuBhuloWDpR8dXy68j",
            "xjX00YO6MCtADv3G+8FPTg4KNqD96zK2XlpxAoGAWxLPxsJM71wnUXloar4X1pZU",
            "H5sKI9x0ivkug/DwaDbXZP4CO5f09L1yvQhXN1hQVqBKENXFOKgT1ZkKc5aIo+Py",
            "8GkcvwcQLsXUrli1JW0dbTUYYFH+lbvB7Kpn78Lxgdwv0vYFbTjAeW1Pgyzq9G97",
            "6FI0qUia8eWEUNibK1k="
        ]
        info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_parts) + "\n-----END PRIVATE KEY-----"
        creds = service_account.Credentials.from_service_account_info(info)
        gc = gspread.authorize(creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
        return gc.open("Hao_Harbour_DB").get_worksheet(0)
    except Exception as e:
        st.error(f"连接失败: {e}")
        return None

# --- 2. 界面切换 ---
tab1, tab2 = st.tabs(["✨ 发布新房源", "🗄️ 房源管理库"])

# --- Tab 1: 发布界面 ---
with tab1:
    st.subheader("📝 录入房源信息")
    
    with st.form("listing_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("房源名称 (例: River Park Tower)")
            region = st.selectbox("伦敦区域", ["东伦敦", "西伦敦", "南伦敦", "北伦敦", "中伦敦"])
            rooms = st.selectbox("户型", ["Studio", "1房", "2房", "3房", "4房+"])
        
        with col2:
            price = st.number_input("租金 (月租 £)", min_value=0, step=100)
            available_date = st.date_input("起租时间", datetime.now())
        
        en_desc = st.text_area("英文描述 (English Description)", height=150, help="粘贴 Rightmove 或官方的英文描述")
        
        # AI 按钮放在表单内或外均可，这里用 st.form 的提交逻辑
        submitted = st.form_submit_button("🎨 生成海报预览 & 保存数据")

    if submitted:
        with st.spinner("DeepSeek 正在翻译并生成中文总结..."):
            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一个伦敦房产专家。请将英文描述翻译成吸引人的中文。要求：包含租金、户型、周边交通。使用Emoji增加吸引力。"},
                        {"role": "user", "content": en_desc}
                    ]
                )
                zh_summary = response.choices[0].message.content
                
                st.divider()
                st.subheader("🖼️ 海报预览内容")
                st.success("AI 中文总结生成成功！")
                st.markdown(zh_summary)
                
                # 模拟六张照片展示
                st.write("📷 房源照片预览 (最近上传的 6 张):")
                cols = st.columns(3)
                for i in range(6):
                    cols[i % 3].image("https://via.placeholder.com/300x200.png?text=Room+Photo", use_container_width=True)
                
                # 保存到 Google Sheets
                ws = get_worksheet()
                if ws:
                    new_row = [str(datetime.now().date()), title, region, rooms, price, "", zh_summary]
                    ws.append_row(new_row)
                    st.balloons()
                    st.info("数据已成功存入 Hao_Harbour_DB")
            except Exception as e:
                st.error(f"发布出错: {e}")

# --- Tab 2: 管理界面 ---
with tab2:
    st.subheader("📊 现有房源管理")
    ws = get_worksheet()
    if ws:
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            # 房源搜索筛选
            search_query = st.text_input("🔍 搜索房源名称或区域")
            if search_query:
                df = df[df['title'].str.contains(search_query, case=False) | df['region'].str.contains(search_query, case=False)]
            
            st.dataframe(df, use_container_width=True)
            
            # 删除/编辑功能（简化演示）
            if st.button("🗑️ 清空最后一条记录"):
                ws.delete_rows(len(data) + 1)
                st.rerun()
        else:
            st.warning("数据库目前是空的。")
