import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

st.set_page_config(page_title="Hao Harbour Properties", layout="wide")

# --- 1. 详情弹窗逻辑 ---
@st.dialog("房源详情")
def show_details(item):
    # 立即展示核心内容，不等待数据库更新
    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    st.markdown(item.get('description', '暂无描述'))
    st.divider()
    
    # 微信 ID 与 下载
    col_wa, col_dl = st.columns(2)
    with col_wa:
        st.code("HaoHarbour_UK", language=None)
        st.caption("点击复制微信客服 ID")
    with col_dl:
        try:
            img_data = requests.get(item['poster-link']).content
            st.download_button("💾 下载房源海报", data=img_data, file_name=f"{item['title']}.jpg")
        except: pass

    # --- 浏览量增加 (静默处理，不报错) ---
    try:
        conn_update = st.connection("gsheets", type=GSheetsConnection)
        df_update = conn_update.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_update.columns:
            # 只在这一行加 1
            idx = df_update.index[df_update['title'] == item['title']].tolist()
            if idx:
                df_update.at[idx[0], 'views'] = int(df_update.at[idx[0], 'views']) + 1
                conn_update.update(worksheet="Sheet1", data=df_update)
    except: pass

# --- 2. 主页面渲染 ---
st.title("🏡 Hao Harbour | Exclusive London Living")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 使用较长的 TTL (缓存)，确保加载速度
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 排序：将精选置顶，日期次之
    if 'is_featured' in df.columns:
        df = df.sort_values(by=['is_featured', 'date'], ascending=[False, False])
    else:
        df = df.sort_values(by='date', ascending=False)

    # 循环展示
    cols = st.columns(3)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                # 如果是精选房源，在图片上方加个小标签
                if row.get('is_featured', False):
                    st.markdown("⭐ **精选推荐 (Featured)**")
                
                st.image(row['poster-link'], use_container_width=True)
                st.write(f"**{row['title']}**")
                st.write(f"📍 {row['region']} | 🛏️ {row['rooms']}")
                st.write(f"💰 **£{row['price']}**/pcm")
                
                if st.button("查看详情", key=f"btn_{idx}", use_container_width=True):
                    show_details(row)
except Exception as e:
    st.error("房源数据加载中，请稍后刷新...")
