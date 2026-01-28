import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
import json

# 1. 强制清理：不要依赖任何变量名，直接重新定义
# 请把【刚才新下载的 JSON】内容粘贴在下面
MY_NEW_JSON = r'''
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

# 使用 cache_resource 确保凭据被物理刷新
@st.cache_resource
def get_verified_gspread_client():
    info = json.loads(MY_NEW_JSON)
    # 再次强调：这里一定要处理私钥中的换行符，否则会报 Signature 错误
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = service_account.Credentials.from_service_account_info(info)
    scoped = creds.with_scopes([
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    return gspread.authorize(scoped)

st.title("🏡 Hao Harbour 数据管理")
SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

if st.button("🔥 强制刷新数据并重置连接"):
    # 点击按钮时，强制清除缓存，让程序必须重新读取 MY_NEW_JSON
    st.cache_resource.clear()
    
    client = get_verified_gspread_client()
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_records()
        st.success(f"成功！当前登录账号: {client.auth._service_account_email}")
        st.dataframe(pd.DataFrame(data))
    except Exception as e:
        # 如果还是报错，这里会打印出【当下真正导致失败的邮箱】
        actual_email = json.loads(MY_NEW_JSON).get('client_email')
        st.error(f"访问被拒绝！请确认表格是否分享给了: {actual_email}")
        st.write(f"详细错误调试信息: {e}")
