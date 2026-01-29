import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
from datetime import datetime

# --- 1. 核心认证 (物理拼装版) ---
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
tab1, tab2 = st.tabs(["✨ 智能发布海报", "🗄️ 房源库管理"])

if 'zh_summary' not in st.session_state:
    st.session_state.zh_summary = ""

# --- Tab 1: 智能发布 (结构微调确保稳定) ---
with tab1:
    with st.container(border=True):
        st.subheader("1. 基础信息录入")
        c1, c2, c3 = st.columns(3)
        title = c1.text_input("房源名称", key="new_title")
        region = c2.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"], key="new_region")
        price = c3.number_input("租金 (£/月)", min_value=0, key="new_price")
        
        en_desc = st.text_area("2. 粘贴英文描述", height=150, key="new_en_desc")
        
        if st.button("🤖 智能提取中文文案"):
            if en_desc:
                with st.spinner("DeepSeek 正在解析..."):
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
                    ai_res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是一个伦敦房产专家。总结英文描述为中文要点。"},
                                  {"role": "user", "content": en_desc}]
                    )
                    st.session_state.zh_summary = ai_res.choices[0].message.content
            else:
                st.warning("请先输入英文描述")

        final_zh_desc = st.text_area("3. 编辑并确认中文文案", value=st.session_state.zh_summary, height=200, key="final_desc_input")
        st.file_uploader("4. 添加照片 (预览)", accept_multiple_files=True, type=['png', 'jpg'], key="new_pics")
        
        if st.button("🚀 正式发布并存档", key="publish_btn"):
            ws = get_worksheet()
            if ws:
                ws.append_row([str(datetime.now().date()), title, region, "待定", price, "", final_zh_desc, 0])
                st.balloons()
                st.success("发布成功！")

# --- Tab 2: 房源管理 (修复重复 ID 报错) ---
with tab2:
    ws = get_worksheet()
    if ws:
        # 实时拉取数据
        all_data = ws.get_all_records()
        df = pd.DataFrame(all_records := all_data)
        
        st.subheader("🔍 房源库检索")
        keyword = st.text_input("搜索名称或区域", placeholder="输入搜索内容...", key="mgmt_search")
        
        # 过滤数据
        if keyword:
            display_df = df[df['title'].astype(str).str.contains(keyword, case=False) | 
                            df['region'].astype(str).str.contains(keyword, case=False)]
        else:
            display_df = df

        st.write(f"共找到 {len(display_df)} 条记录")

        # 核心修复：遍历 display_df 时使用唯一的 identifier
        for idx, row in display_df.iterrows():
            # 计算原始行号 (标题行占 1 行，索引从 0 开始，所以 +2)
            real_row_num = idx + 2
            
            # 使用房源标题+原始行号创建唯一 key，彻底解决 build_duplicate_form_message 报错
            unique_key = f"form_{row['title']}_{real_row_num}"
            
            with st.expander(f"{'⭐' if row.get('is_featured')==1 else ''} {row['title']} - £{row['price']}"):
                with st.form(key=unique_key):
                    c1, c2 = st.columns(2)
                    upd_price = c1.number_input("价格 (£)", value=int(row['price']), key=f"p_{unique_key}")
                    upd_region = c2.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"], 
                                             index=["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"].index(row['region']),
                                             key=f"r_{unique_key}")
                    upd_desc = st.text_area("文案", value=row['description'], height=150, key=f"d_{unique_key}")
                    
                    bc1, bc2, bc3 = st.columns(3)
                    if bc1.form_submit_button("💾 保存修改"):
                        ws.update_cell(real_row_num, 5, upd_price) # 第5列价格
                        ws.update_cell(real_row_num, 3, upd_region) # 第3列区域
                        ws.update_cell(real_row_num, 7, upd_desc) # 第7列描述
                        st.success("已保存！")
                        st.rerun()

                    if bc2.form_submit_button("⭐ 切换精选"):
                        new_f = 0 if row.get('is_featured') == 1 else 1
                        ws.update_cell(real_row_num, 8, new_f) # 第8列精选
                        st.rerun()

                    if bc3.form_submit_button("🗑️ 删除房源"):
                        ws.delete_rows(real_row_num)
                        st.warning("房源已下架")
                        st.rerun()
