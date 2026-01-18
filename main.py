import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🚀 Hao Harbour 云端数据库测试")

# 1. 初始化连接 (会读取你刚才在 Secrets 填写的配置)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("✅ 成功连接到 Google Sheets 引擎！")
except Exception as e:
    st.error(f"❌ 连接引擎失败，请检查 Secrets 配置。错误信息: {e}")

# 2. 读取现有数据 (测试读取权限)
st.subheader("当前表格数据预览")
try:
    # 注意：worksheet 名称必须和你表格下方的标签名一致，通常是 "Sheet1"
    df = conn.read(worksheet="Sheet1")
    st.dataframe(df)
except Exception as e:
    st.warning("目前表格可能是空的，或者读取失败。")

# 3. 写入测试数据 (测试写入权限)
st.subheader("写入测试")
test_title = st.text_input("输入一个房源名称进行测试", value="Lexington Gardens Test")

if st.button("📝 点我写入一行数据到表格"):
    try:
        # 构建一行新数据
        new_data = pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": test_title,
            "region": "西伦敦",
            "rooms": "2房",
            "price": 3358,
            "poster_link": "https://example.com/test.png"
        }])
        
        # 获取旧数据并合并
        existing_data = conn.read(worksheet="Sheet1")
        # 如果现有数据全是空的，直接用新数据
        if existing_data.empty or existing_data.dropna(how='all').empty:
            updated_df = new_data
        else:
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 写回 Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
        
        st.balloons()
        st.success("🎉 太棒了！数据已成功写入 Google Sheets！快去检查你的表格。")
        
        # 刷新页面显示新数据
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 写入失败！这通常是因为机器人账号没有表格的 'Editor' 权限。错误详情: {e}")
