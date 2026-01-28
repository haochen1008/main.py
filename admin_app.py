import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import json

# --- 1. 核心数据区 ---
# 请直接把下载的 JSON 文件内容【原封不动】贴在下面两个 r''' 之间
raw_json_str = r'''
{
  "type": "service_account",
  "project_id": "canvas-voltage-278814",
  "private_key_id": "bc22b4f4c934664f5c55d3840be9501bab711f0f",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDQoHCtdlGu7q8q\naNZyjjzYBg3TX1mfTwUjaMHQJXmKlzK1PQdDrvwFRZTbDV3ir6fbITCfRkmGXvHh\njSzQ3ElKxvvFIqxZufeHyVfrczaoTsCr5Epg6dKxiF4CoV4ivQGD/6qPy/VIzkul\ngH1KYB8Y+mphhfyQ2IurAWAjp054vM4JhgFYq6yA4T/riZjYt4rpnsQyD/Dky/7H\ns2nJ+l8XNJhWKUyeKAMymSgwcn9Sd7Et9YqPL65DXcp5eaYmhVkYy9kMTZkIxb/u\n946WrIbPx0BmS7l1h83nqX2zf7Vt3jzjitiu0kCSl6D2V/LP3rWQP/EAM8TicbZm\nmvE4nErZAgMBAAECggEAHOX8daqsCeU6Ek/PVLLrLqk4BQ1yJqUVeyApqKFoQpBL\nD9vSQ8fbVQecZPNnC911DN9+ErHzwU8phiq+CHhbFqaVfWseIJen+AEl0pF1Ar9V\n5PmMa/w3mSvgidC8b2dq7FPf1mdUJK+evuAbes/xvs4BKl0a7R1xy1A3dvjX39VX\nLWQ9MSsGA8CPy6tkLTptYlWy4QUwVo9dNZq4RphdWNvzp9lQ/FCjEq10efsapmg6\nv0KKSTnqKeQ96H0RV1fCPEjQn01Lx8kb+2D4MvbP2/Peme0OaMompqqrdbZjCPY/\nycxZldHNQaloOHWAl5MDtt2vr/PqZPT44+zCHc1u+QKBgQD4GkVfZRnyhbpyezDM\n08Kc6Wjrt4IDx0up4tLsCZM8iQwJQkSJrflkWi63DHmYAvo+OxpsLp6Gwx4lWRxI\n9GBVw4g598PJJVgV4LdP+xt76afGML3lEpKqcbWQenUoiu/YieTxOHwlcqVdwMWQ\nHmxYmdM229e2XspMSXy9h4NNhwKBgQDXRH1NexezIoCpHFVq0xUBCuVUFmLMWpdK\n/ylOntOmfztwO4P0lKfI/t2igaomt84ub9vO6oQWMQ0sLx0vgA749EhjzOma9GE0\n169ryTjds21LO9L3eMTDVPpaSjDwDmElH9WF8RSJ6OGSSTT1E9HP6Mr0wHx6Gd2B\nqecKneC8nwKBgQC58BZltAOKOqbM/X5JQ7rqlhNH9TO/WTFflNq2g0aRa7RVjBCJ\njpUFnIC+Nt86CaE52lmnEhlErh59pxcHpf48yFnj98gHi7FEVDGOA4dJioduhUEL\n2KuKicWlDeGYDOhLxKyMC+Ueu5krdjmaFPLmRAKDbqdvygKawch20oSZKQKBgAmZ\nCiUsOdBI14eytbQ/mQ4k2Di5jsoht+EmI0dYGYOw5IuKe8Wp4xk5E9StB1MWmuDD\nJ/+/wQfkQ/wWVazKfuBms9uPRVMdVkAu5alenWR1HYhfMHbMMamr3kWsTSZG3dnz\n42dHam0DrxsAnJXYvmAQtwvWkTY4dQHU+3Iju+NtAoGAKG7mBPEb9POKjSFkmqBG\n1O3hB4BjLyKTRFMab4fUWKdKQ6rxDuGPLl/ozGtcrxC3z+Ue4yP3IwA7uM87T/se\nPDIUu6pQdxwN+MVxxKST3Kb+5Ll5Gbc94W7GeFaizkmKMcm6otmFqvsIiy3bQFWE\nO2UeSMUALckwZGZIfJa0X+o=\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit-bot@canvas-voltage-278814.iam.gserviceaccount.com",
  "client_id": "117914675899035990089",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-bot%40canvas-voltage-278814.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
'''

def get_gsheet_client():
    try:
        # 解析 JSON 字符串
        info = json.loads(raw_json_str)
        
        # 【关键修正】：强制修复可能存在的换行符转义问题，解决 Invalid JWT Signature
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        creds = service_account.Credentials.from_service_account_info(info)
        scoped = creds.with_scopes([
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(scoped)
    except Exception as e:
        st.error(f"密钥解析失败: {e}")
        return None

# --- 2. 展示逻辑 ---
st.title("🏡 Hao Harbour 管理中心")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("刷新现有房源"):
    client = get_gsheet_client()
    if client:
        try:
            # 打开表格并读取第一张工作表
            sheet = client.open_by_key(SHEET_ID).sheet1
            data = sheet.get_all_records()
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            st.success("数据加载成功！")
        except Exception as e:
            # 如果依然报错，会显示在这里
            st.error(f"连接表格失败: {e}")
