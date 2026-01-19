import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import urllib.parse

st.set_page_config(page_title="Hao Harbour | Exclusive London Living", layout="wide")

# --- 1. 详情页交互逻辑 ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    st.write(f"### {item['title']}")
    st.write(f"💰 **Monthly Rent: £{item['price']}**")
    st.markdown(item.get('description', '暂无详细亮点说明'))
    st.divider()

    # 功能按钮区
    st.write("#### 📞 快捷咨询与工具")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.code("HaoHarbour_UK", language=None)
        st.caption("点击复制微信客服")
    with col2:
        phone = "447000000000" # 请在此处修改你的 WhatsApp 号码
        wa_url = f"https://wa.me/{phone}?text=" + urllib.parse.quote(f"Hi, I'm interested in {item['title']}")
        st.link_button("💬 WhatsApp咨询", wa_url, use_container_width=True)
    with col3:
        st.link_button("📞 拨号联系", f"tel:+{phone}", use_container_width=True)

    col4, col5 = st.columns(2)
    with col4:
        map_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(item['title'] + ', London')}"
        st.link_button("📍 Google Maps 导航", map_url, use_container_width=True)
    with col5:
        try:
            img_data = requests.get(item['poster-link']).content
            st.download_button("📥 下载保存海报", data=img_data, file_name=f"{item['title']}.jpg", use_container_width=True)
        except: st.write("图片暂无法下载")

    # 静默更新浏览量
    try:
        conn_u = st.connection("gsheets", type=GSheetsConnection)
        df_u = conn_u.read(worksheet="Sheet1", ttl=0)
        if 'views' in df_u.columns:
            df_u.loc[df_u['title'] == item['title'], 'views'] += 1
            conn_u.update(worksheet="Sheet1", data=df_u)
    except: pass

# --- 2. 主页面装饰与 Banner ---
st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
        <h1 style="color: #1a1a1a; margin-bottom: 5px;">HAO HARBOUR</h1>
        <p style="color: #bfa064; font-weight: bold; letter-spacing: 2px;">EXCLUSIVE LONDON LIVING</p>
    </div>
""", unsafe_allow_html=True)

# --- 3. 数据渲染 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    # 排序逻辑：精选优先，日期次之
    if 'is_featured' in df.columns:
        df = df.sort_values(by=['is_featured', 'date'], ascending=[False, False])
    else:
        df = df.sort_values(by='date', ascending=False)

    cols = st.columns(3)
    for i, (idx, row) in enumerate(df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                # 🌟 Featured 标签渲染
                if row.get('is_featured', False):
                    st.markdown("""
                        <div style="background: rgba(255, 75, 75, 0.9); color: white; 
                                    padding: 2px 10px; border-radius: 5px; font-size: 12px; 
                                    font-weight: bold; width: fit-content; margin-bottom: 5px;">
                            🌟 FEATURED PROPERTY
                        </div>
                    """, unsafe_allow_html=True)
                
                st.image(row['poster-link'], use_container_width=True)
                st.write(f"**{row['title']}**")
                st.caption(f"📍 {row['region']} | {row['rooms']} | £{row['price']}/pcm")
                
                if st.button("查看详情 / View Details", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
except:
    st.error("房源列表加载中，请稍后刷新...")
