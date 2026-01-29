import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="Hao Harbour 综合管理", layout="wide")
st.title("🏡 Hao Harbour 数据与 AI 管理系统")

# 1. 物理拼装私钥（确保认证不报错）
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

def get_worksheet():
    try:
        info = dict(st.secrets["gcp_service_account"])
        info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_parts) + "\n-----END PRIVATE KEY-----"
        creds = service_account.Credentials.from_service_account_info(info)
        gc = gspread.authorize(creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
        
        # --- 重点：直接用名字打开，不用手动填 ID 避免 0 和 O 输错 ---
        sh = gc.open("Hao_Harbour_DB") 
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"❌ 依然报错: {e}")
        return None

# 初始化界面
ws = get_worksheet()
if ws:
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    st.success("🎉 终于大功告成了！ID 的 0 和 O 问题已通过名字识别完美绕过！")
    
    tab1, tab2 = st.tabs(["📊 实时看板", "🤖 AI 分析"])
    
    with tab1:
        st.dataframe(df, use_container_width=True)
        
    with tab2:
        if st.button("🚀 使用 DeepSeek 分析"):
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], base_url=st.secrets["OPENAI_BASE_URL"])
            # 获取第一行的描述作为测试
            desc = df.iloc[0].get('description', '无描述')
            res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":f"总结房源: {desc}"}])
            st.write(res.choices[0].message.content)
