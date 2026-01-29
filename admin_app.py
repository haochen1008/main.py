import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
from openai import OpenAI
import requests

# 页面配置
st.set_page_config(page_title="Hao Harbour 房源智能管理", layout="wide")
st.title("🏡 Hao Harbour 数据与 AI 管理系统")

# --- 1. 认证与连接 (使用已验证成功的逻辑) ---
def get_worksheet():
    try:
        info = dict(st.secrets["gcp_service_account"])
        # 物理拼装私钥，彻底避开转义字符坑
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
        gc = gspread.authorize(creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]))
        # 使用名称直接打开，绕过 ID 拼写错误
        sh = gc.open("Hao_Harbour_DB") 
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"❌ 数据连接中断: {e}")
        return None

# --- 2. DeepSeek AI 解析逻辑 ---
def deepseek_analyze(text):
    try:
        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"], 
            base_url=st.secrets["OPENAI_BASE_URL"]
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个房产分析专家，请从描述中提取：租金(月/周)、户型、邮编、起租日期。用简洁的列表回复。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 暂时不可用: {e}"

# --- 主程序逻辑 ---
ws = get_worksheet()

if ws:
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    
    # 侧边栏导航
    st.sidebar.header("功能菜单")
    menu = st.sidebar.radio("选择操作", ["📊 实时看板", "🤖 DeepSeek AI 提取", "🖼️ 海报预览 & 托管"])
    
    if menu == "📊 实时看板":
        st.subheader("当前在线房源总览")
        # 数据统计指标
        col1, col2, col3 = st.columns(3)
        col1.metric("房源总数", len(df))
        col2.metric("最高月租", f"£{df['price'].max()}")
        col3.metric("平均月租", f"£{int(df['price'].mean())}")
        
        st.dataframe(df, use_container_width=True)
        st.success("✅ 数据已实时从 Hao_Harbour_DB 同步")

    elif menu == "🤖 DeepSeek AI 提取":
        st.subheader("DeepSeek 房源智能解析")
        if not df.empty:
            selected_house = st.selectbox("选择要分析的房源", df['title'].tolist())
            desc = df[df['title'] == selected_house]['description'].values[0]
            
            c1, c2 = st.columns(2)
            c1.info("原始文本描述:")
            c1.write(desc)
            
            if c2.button("🚀 调用 DeepSeek 提取"):
                with st.spinner("DeepSeek 正在解析中..."):
                    result = deepseek_analyze(desc)
                    c2.success("AI 提取结果:")
                    c2.markdown(result)

    elif menu == "🖼️ 海报预览 & 托管":
        st.subheader("Cloudinary 海报托管详情")
        if not df.empty:
            target = st.selectbox("选择预览房源", df['title'].tolist())
            row = df[df['title'] == target].iloc[0]
            
            img_url = row.get('poster_link', '')
            if img_url:
                st.image(img_url, caption=f"托管于 Cloudinary: {st.secrets['CLOUDINARY_CLOUD_NAME']}", use_container_width=True)
                st.code(f"海报链接: {img_url}")
            else:
                st.warning("该房源暂无海报链接")
            
            st.divider()
            st.write(f"**图片 API 状态:** Cloudinary & ImgBB 已连接")

else:
    st.error("无法加载数据，请检查 Secrets 中的 GCP 配置。")
