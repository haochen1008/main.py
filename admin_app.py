import streamlit as st
import pandas as pd
import cloudinary, cloudinary.uploader
from google.oauth2 import service_account
import gspread
from datetime import datetime

# 1. 基础页面设置
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# 2. 这里是你的 Google 身份凭据（已修正换行符问题）
# 直接硬编码在这里，彻底绕过 Secrets 的格式 Bug
google_credentials = {
    "type": "service_account",
    "project_id": "canvas-voltage-278814",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC+wv9F4YTB4NJM\noacbmuJpkVevElYXii2lFcx7PafqgAKWJfTJ0r7U/lUZ/IJT2h4A8foSxaTgmdYD\ngH4VqlZrn2eG67eAqr3clb94HzNiEu2xxKBsLn9tT5J4bP4AZRHkdwuxiHyXCj+z\nxDjRDwx+A454URrK4/0r27Go/JuqtffeD45aH8z++YDgLBbCaef8AiWrM1ANEAF7\np4Zm0Qi0r4/faQ2VVopIpbNKa+FiRhPhjfMbTZsSinjmlHHn9QRnh9Lbaoff+GSu\ngL5jfCZFqd9mYexvkkfVrHok6ZfMb1GpvCH+BXQZJppLjzZLmO1k0ClUAFpL0W9q\nCS6dblX5AgMBAAECggEAMYd/sC01wwEUmUD/mnNEhhRup84i/EmsQEjApt8DUiea\nhFGmlSBa3AKNJgoh7JOdZrFtNKKMhKRspMwf8JAhkB/7SVS6eHXchgF7jTzMopI3\nlQhwfqYz/7XBWfMyn/eeBavDJX1CnBTVJV+1QNKfc7iIrUShqDw558FLB41O/at9\n94IIvQosRF9C//qx0U1tAYzkwwC4lWr2LLt7on6lnh6SgGfXC/j9q3E+swQeA08n\nuoy+fMtjo20RVFT7cEGLcKY8m6NUA4gSo+uG1WehW9fT5FFaa2NCr83an2o5qtGa\nbX0Jv53SmMIHhDGkq+jjoI2vcnk4a9NhpgyQ+ty04QKBgQD4086rEa6jTg4kjDjb\ncgCJb4SNQ7duMLfzX+Zwb9XdQRaxaRM4O/K15R4omAbyyHsXd/do0knDbp78xSG4\nioWwNafLCUa9vdk/EEtIHxi/BrviyAgU2MUwNdrH+pDHNzwKVfN+wdQao0ETcDaQ\nO1vZiI4jzdJT1frEJbdnMfbf8wKBgQDEQrN22t+CxwMUmzyAlGzDyOGjPOpQ+oAU\nffDctIJzHOB45WPNlsWI+nlOsd7WqITkb4njFfSM6o8ZaqaZ/kcS7Zt32GY7aBuv\nIFe47lseBC1rSPBOyrXFnWdiSgxfIV4MAToGlIqfDGTcVlWBocmKoZ/HqHi5PEAj\n1+eEoU0ZYwKBgGvbpCITMBgppYfCIIM/D2yDonl5ePGSvKoKT+E9GP8nT6bnXSVr\nFvIxtrjx7VEgBftOTThqrv6/3LrE2LEdmoWfPHSOONPWj2z+qyNAF4H2cUsEWjxv\nGkqjjYpR2qAAGU6Bo2K2sjI5weOjKIOst0u8HaD3fsxIXMLZdn6M8e5xAoGADQqt\nqFFFFwiogL8MFzNFwwDfVZyfqX/r8PCph9EK9iFOHVqI9kl1mPOkCgGx4CvUoOV0\nkT2NQav4lGTM62DFUlGtyhn8OShi5FMowJb1bPLXNy8809vItGh5BstlUi/Wibe\ntz85svX84dNu3S1mGitBVeAxHYYOcRNQ1DRvzicCgYEAnpar/8Eye+gDq64D/aFW\ndSteGhJw/PdCEf6i6L+2Ugq4XxfHJkmeY+WMWS2XRC8sILR1MkiHBUOWq1MQnYxW\nSwB1eRoUpzNVnbMZHTjx4CxK4ryzuPPLcEV75BwZorLYmzB7Mr6nq0cYKN8Dp4eK\n+wGoiPF364CBMnbEBC4V2xQ=\n-----END PRIVATE KEY-----\n",
    "client_email": "haoharbour-sheets@canvas-voltage-278814.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}

# 3. 云端连接配置
cloudinary.config(
    cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key=st.secrets["CLOUDINARY_API_KEY"],
    api_secret=st.secrets["CLOUDINARY_API_SECRET"]
)

SHEET_ID = "1wZj0JpEx6AcBsem7DNDnjKjGizpUMAasDh5q7QRng74"

def get_google_sheet():
    creds = service_account.Credentials.from_service_account_info(google_credentials)
    scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    client = gspread.authorize(scoped_creds)
    return client.open_by_key(SHEET_ID).sheet1

st.title("🏡 Hao Harbour 房源管理")
tab1, tab2 = st.tabs(["🚀 发布新房源", "📊 管理现有房源"])

with tab1:
    with st.form("upload_form"):
        n_title = st.text_input("房源名称")
        n_price = st.number_input("月租 (£)", value=2500)
        n_pics = st.file_uploader("上传图片", type=['jpg', 'png'])
        if st.form_submit_button("发布房源"):
            if n_title and n_pics:
                try:
                    with st.spinner("正在上传并保存..."):
                        # 1. 上传图片到 Cloudinary
                        img_res = cloudinary.uploader.upload(n_pics)
                        img_url = img_res['secure_url']
                        # 2. 写入 Google Sheets
                        sheet = get_google_sheet()
                        sheet.append_row([datetime.now().strftime("%Y-%m-%d"), n_title, n_price, img_url])
                        st.success("🎉 发布成功！")
                except Exception as e:
                    st.error(f"发布失败: {e}")

with tab2:
    if st.button("🔄 刷新房源看板"):
        try:
            sheet = get_google_sheet()
            data = sheet.get_all_records()
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        except Exception as e:
            st.error(f"加载数据失败: {e}")
