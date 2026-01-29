import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
from datetime import datetime

# --- 1. 核心认证 (物理拼装版，确保稳定) ---
def get_worksheet():
    try:
        info = dict(st.secrets["gcp_service_account"])
        key_parts = ["MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCRayoKdXw38HlF", "6J23Bbyq7zAzCWQ5OAtzk0/fOhbnFUHJTMOF1njbBw92x9etYoDt5WbBUwbexaQE", "6mTmvNU0pIGEH+iUWxvkb0VNWe3o1AceLLyDECR8p+srO04Un9hP9N0k+3SzNUFo", "xTSQCMg+GVDLJN2TLTZ3MaAuJY+UtZ+tk0K01PMZGRGu8Jl0iSZhlsbZeTSptzMJ", "UIZRnbIu8HVGVfZYGWEb1sWmUBMKsJAkr5nWPDCTgQex98rdrgSKNxT+I8x6nQMz", "pkqVTcAOlShz8bXr85C/g+t8wFMSFZKi0KGdweZY1pgTkRe7589V/ne4omfK0oqu", "q7BLqPYtAgMBAAECgf9yRxG3eT+Az4zYsAWlrSuOeY9l/67YwQF2CB/3nDAprTQ+", "QAxnf2HIUA4mEdTysdwMO1ptOvuiY8DOZ2paAtvzjg2ypW/PqSQd4e9R25K4PxT5", "h0UvZO1bpLOOCFwWgVAcEjKZ1MEmIzonCN0Kx22aqtRmJblpc4uwgcZ53MHmN1qH", "UoSB1zw9c6EEoevxDAlve7yuVE5BU0kHtyaQANTShDjbLMFt2yvRBY4ZSuqJVjKG", "BWt6gTPyTHm3JcMxNOkEaxT/4eJytU1GUuqxShQf4rRCfeaCCcBPnzWl9LigYQ1O", "+s3b6rxjioi2p+nzgzhVpQVnaa7eGxojoaNpkukCgYEAwytmFQ1oLK+EzET6u2Bt", "O/qB2sxn3iKFaHMRBF2HEAOmmwCxqipvswiQmrV2pX1t+TQd+kk5z6iEpgsmm9HY", "mdUv9QBN23TmOfS1UJjLkeKmRfanhr700QpwW29yuL/RBpvSanXDnreiFw5gMT+/", "/AODyVyKDzPUwleamZtsvrUCgYEAvr4iMO8B9u6j4EPVa8XKl2ho2tm9qgrviIbd", "dvu4itmgECC/BWEsvJhgoqm1jG8A+KMhf5oUZJKrwMB0EjOM+r43PzjYfY+CvtAz", "Mfea+rbhCWootwt9YWeqkBay00jtVe0kKMcaXzfcNUucDRDa8+8RLhUunBx6SzGj", "BW3gjJkCgYB4ZpeNOT4hAw6brZo4ah45OCtPvXX+VbGTZBkFZmVh/b6UNPNllNRf", "0FLU/kl5gk2LxRkRRIdDkiRzAsIIsoY7MIdrT4q4bf9xlYMde4VqNDZ7RtTGjZse", "MqBp5/EQBFWBDDPctVW+3m5CZv30o+1eHRT57frFsiX41m5rgLSvWQKBgDvGZfyj", "yh/SZXTQjT96+qQ8Si/bcL6rMqm8agbxl8GbtbeYK4TKETUBI7eWK5jY6JsCtGrC", "pIVoGX8MUNOraBDkL3gWnnGq2bRmlsSf7eeIDDnhFOVYKnCuBhuloWDpR8dXy68j", "xjX00YO6MCtADv3G+8FPTg4KNqD96zK2XlpxAoGAWxLPxsJM71wnUXloar4X1pZU", "H5sKI9x0ivkug/DwaDbXZP4CO5f09L1yvQhXN1hQVqBKENXFOKgT1ZkKc5aIo+Py", "8GkcvwcQLsXUrli1JW0dbTUYYFH+lbvB7Kpn78Lxgdwv0vYFbTjAeW1Pgyzq9G97", "6FI0qUia8eWEUNibK1k="]
        info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_parts) + "\n-----END PRIVATE KEY-----"
        creds = service_account.Credentials.from_service_account_info(info)
        gc = gspread.authorize(creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
        return gc.open("Hao_Harbour_DB").get_worksheet(0)
    except: return None

# --- 2. 界面设计 ---
st.title("🏡 Hao Harbour 房源智能管理")
tab1, tab2 = st.tabs(["✨ 智能发布海报", "🗄️ 房源库管理"])

# 初始化 Session State (用于存储 AI 提取的临时文案)
if 'zh_summary' not in st.session_state:
    st.session_state.zh_summary = ""

# --- Tab 1: 智能发布 ---
with tab1:
    with st.container(border=True):
        st.subheader("1. 基础信息录入")
        c1, c2, c3 = st.columns(3)
        title = c1.text_input("房源名称", placeholder="例: River Park Tower")
        region = c2.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        price = c3.number_input("租金 (£/月)", min_value=0)
        
        en_desc = st.text_area("2. 粘贴英文描述", height=150)
        
        if st.button("🤖 智能提取中文文案"):
            if en_desc:
                with st.spinner("AI 正在解析并总结..."):
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
                    ai_res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是一个伦敦房产专家。请把英文描述翻译成吸引人的中文总结，包含户型、交通、租金和亮点。使用 Emoji。"},
                                  {"role": "user", "content": en_desc}]
                    )
                    st.session_state.zh_summary = ai_res.choices[0].message.content
            else:
                st.warning("请先粘贴英文描述")

        # 允许用户编辑 AI 生成的结果
        final_zh_desc = st.text_area("3. 编辑/确认中文文案", value=st.session_state.zh_summary, height=200)
        
        uploaded_files = st.file_uploader("4. 添加照片 (最多6张)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        
        if st.button("🚀 正式发布并存档"):
            ws = get_worksheet()
            if ws:
                # 写入格式: 日期, 名称, 区域, 户型(略), 价格, 图片链接(略), 描述, 精选(0)
                ws.append_row([str(datetime.now().date()), title, region, "待定", price, "", final_zh_desc, 0])
                st.balloons()
                st.success("房源已成功发布并存档！")

# --- Tab 2: 房源管理 ---
with tab2:
    ws = get_worksheet()
    if ws:
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        for index, row in df.iterrows():
            with st.expander(f"{'⭐' if row.get('is_featured') == 1 else ''} {row['title']} - {row['region']} (£{row['price']})"):
                # 编辑模式
                with st.form(key=f"edit_form_{index}"):
                    new_price = st.number_input("修改租金", value=int(row['price']), key=f"p_{index}")
                    new_desc = st.text_area("修改描述", value=row['description'], key=f"d_{index}")
                    
                    c1, c2, c3 = st.columns(3)
                    save_btn = c1.form_submit_button("💾 保存修改")
                    feat_btn = c2.form_submit_button("⭐ 切换精选")
                    del_btn = c3.form_submit_button("🗑️ 删除房源")
                    
                    if save_btn:
                        ws.update_cell(index + 2, 5, new_price) # 第5列是 price
                        ws.update_cell(index + 2, 7, new_desc)  # 第7列是 description
                        st.success("修改已保存")
                        st.rerun()
                        
                    if feat_btn:
                        new_status = 0 if row.get('is_featured') == 1 else 1
                        ws.update_cell(index + 2, 8, new_status) # 第8列是 is_featured
                        st.rerun()
                        
                    if del_btn:
                        ws.delete_rows(index + 2)
                        st.rerun()
    else:
        st.error("数据连接失败。")
