import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 设置页面
st.set_page_config(page_title="Hao Harbour 数据库测试", layout="wide")
st.title("🚀 Hao Harbour 云端数据库测试")

# 1. 尝试初始化连接
try:
    # 建立连接
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. 读取测试
    st.subheader("📊 当前表格数据预览")
    # 如果表格完全是空的，这里可能会报错，我们加个 try
    try:
        # worksheet="Sheet1" 必须对应你表格底部的名称
        df = conn.read(worksheet="Sheet1", ttl=0) # ttl=0 确保每次都读最新的
        if df.empty:
            st.info("表格目前是空的，准备写入第一条数据吧！")
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as read_e:
        st.warning(f"读取提示：表格可能尚未初始化或找不到 Sheet1。详细信息: {read_e}")

    # 3. 写入测试
    st.divider()
    st.subheader("✍️ 写入新数据测试")
    test_title = st.text_input("房源名称", value="Lexington Gardens")
    test_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
    test_price = st.number_input("月租", value=3500)

    if st.button("📝 确认写入并同步到云端"):
        with st.spinner("正在同步..."):
            # 创建新行
            new_row = pd.DataFrame([{
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": test_title,
                "region": test_reg,
                "rooms": "2房",
                "price": test_price,
                "poster_link": "https://haoharbour.com/test.png"
            }])
            
            # 读取旧数据
            try:
                old_df = conn.read(worksheet="Sheet1", ttl=0)
                # 合并
                updated_df = pd.concat([old_df, new_row], ignore_index=True)
            except:
                # 如果读取失败（比如完全空白），则新行就是全部数据
                updated_df = new_row
            
            # 执行更新
            conn.update(worksheet="Sheet1", data=updated_df)
            st.balloons()
            st.success("🎉 写入成功！请刷新你的 Google Sheets 查看。")
            # 自动刷新当前页面
            st.rerun()

except Exception as e:
    st.error("❌ 核心连接失败！")
    st.info("排查建议：")
    st.markdown("""
    1. **Secrets 格式**：确保 Secrets 里的 `private_key` 包含了 `-----BEGIN PRIVATE KEY-----`。
    2. **表格权限**：确保表格已分享给机器人邮箱（Editor 权限）。
    3. **表格网址**：确保 Secrets 里的 `spreadsheet` 网址是正确的。
    """)
    st.exception(e)
