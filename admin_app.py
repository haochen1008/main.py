import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd

st.set_page_config(page_title="Hao Harbour 管理", layout="wide")
st.title("🏡 Hao Harbour 数据管理")

def load_data_final_attempt():
    try:
        # 1. 从 Secrets 读取基础配置
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # 2. 这里的私钥片段是根据你提供的 JSON 源码纯手工拆解的
        # 这样避开了所有的换行符转义和空格问题
        key_parts = [
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDQoHCtdlGu7q8q",
            "aNZyjjzYBg3TX1mfTwUjaMHQJXmKlzK1PQdDrvwFRZTbDV3ir6fbITCfRkmGXvHh",
            "jSzQ3ElKxvvFIqxZufeHyVfrczaoTsCr5Epg6dKxiF4CoV4ivQGD/6qPy/VIzkul",
            "gH1KYB8Y+mphhfyQ2IurAWAjp054vM4JhgFYq6yA4T/riZjYt4rpnsQyD/Dky/7H",
            "s2nJ+l8XNJhWKUyeKAMymSgwcn9Sd7Et9YqPL65DXcp5eaYmhVkYy9kMTZkIxb/u",
            "946WrIbPx0BmS7l1h83nqX2zf7Vt3jzjitiu0kCSl6D2V/LP3rWQP/EAM8TicbZm",
            "mvE4nErZAgMBAAECggEAHOX8daqsCeU6Ek/PVLLrLqk4BQ1yJqUVeyApqKFoQpBL",
            "D9vSQ8fbVQecZPNnC911DN9+ErHzwU8phiq+CHhbFqaVfWseIJen+AEl0pF1Ar9V",
            "5PmMa/w3mSvgidC8b2dq7FPf1mdUJK+evuAbes/xvs4BKl0a7R1xy1A3dvjX39VX",
            "LWQ9MSsGA8CPy6tkLTptYlWy4QUwVo9dNZq4RphdWNvzp9lQ/FCjEq10efsapmg6",
            "v0KKSTnqKeQ96H0RV1fCPEjQn01Lx8kb+2D4MvbP2/Peme0OaMompqqrdbZjCPY/",
            "ycxZldHNQaloOHWAl5MDtt2vr/PqZPT44+zCHc1u+QKBgQD4GkVfZRnyhbpyezDM",
            "08Kc6Wjrt4IDx0up4tLsCZM8iQwJQkSJrflkWi63DHmYAvo+OxpsLp6Gwx4lWRxI",
            "9GBVw4g598PJJVgV4LdP+xt76afGML3lEpKqcbWQenUoiu/YieTxOHwlcqVdwMWQ",
            "HmxYmdM229e2XspMSXy9h4NNhwKBgQDXRH1NexezIoCpHFVq0xUBCuVUFmLMWpdK",
            "/ylOntOmfztwO4P0lKfI/t2igaomt84ub9vO6oQWMQ0sLx0vgA749EhjzOma9GE0",
            "169ryTjds21LO9L3eMTDVPpaSjDwDmElH9WF8RSJ6OGSSTT1E9HP6Mr0wHx6Gd2B",
            "qecKneC8nwKBgQC58BZltAOKOqbM/X5JQ7rqlhNH9TO/WTFflNq2g0aRa7RVjBCJ",
            "jpUFnIC+Nt86CaE52lmnEhlErh59pxcHpf48yFnj98gHi7FEVDGOA4dJioduhUEL",
            "2KuKicWlDeGYDOhLxKyMC+Ueu5krdjmaFPLmRAKDbqdvygKawch20oSZKQKBgAmZ",
            "CiUsOdBI14eytbQ/mQ4k2Di5jsoht+EmI0dYGYOw5IuKe8Wp4xk5E9StB1MWmuDD",
            "J/+/wQfkQ/wWVazKfuBms9uPRVMdVkAu5alenWR1HYhfMHbMMamr3kWsTSZG3dnz",
            "42dHam0DrxsAnJXYvmAQtwvWkTY4dQHU+3Iju+NtAoGAKG7mBPEb9POKjSFkmqBG",
            "1O3hB4BjLyKTRFMab4fUWKdKQ6rxDuGPLl/ozGtcrxC3z+Ue4yP3IwA7uM87T/se",
            "nPDIUu6pQdxwN+MVxxKST3Kb+5Ll5Gbc94W7GeFaizkmKMcm6otmFqvsIiy3bQFWE",
            "O2UeSMUALckwZGZIfJa0X+o="
        ]
        
        # 3. 缝合私钥
        inner_key = "\n".join(key_parts)
        creds_info["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{inner_key}\n-----END PRIVATE KEY-----"
        
        # 4. 授权并建立客户端
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        scoped = credentials.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(scoped)
        
        # 5. 打开表格并读取
        sh = gc.open_by_key("1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74")
        return pd.DataFrame(sh.sheet1.get_all_records())
        
    except Exception as e:
        st.error(f"❌ 认证配置出错: {e}")
        return None

# 执行逻辑
if st.button("🚀 暴力同步数据"):
    with st.spinner("正在解析私钥并连接..."):
        df = load_data_final_attempt()
        if df is not None:
            st.success("🎉 终于连接成功了！")
            st.dataframe(df)
