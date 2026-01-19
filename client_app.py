import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
import base64
import requests
from datetime import datetime

# --- 1. 基础页面配置 (保持原先的简洁风格) ---
st.set_page_config(page_title="Hao Harbour | London Living", layout="wide")

# --- 2. 核心 CSS 样式 (保持原先逻辑) ---
st.markdown("""
    <style>
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: -45px; }
    header {visibility: hidden;} 
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .custom-header {
        background-color: #ffffff;
        display: flex;
        align-items: center;
        padding: 5px 20px;
        height: 70px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 20px;
    }
    .logo-img { max-height: 40px; margin-right: 15px; }
    .header-text { border-left: 1px solid #ddd; padding-left: 15px; }
    .header-title { font-family: sans-serif; font-size: 18px; font-weight: bold; color: #1a1a1a; margin: 0; }
    .header-subtitle { font-size: 9px; color: #888; letter-spacing: 2px; margin: 0; }
    
    .stImage > img { border-radius: 12px; }
    .meta-row { display: flex; justify-content: space-between; align-items: center; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 详情弹窗 (简洁版 + Google Maps) ---
@st.dialog("房源详情")
def show_details(item):
    st.image(item['poster-link'], use_container_width=True)
    
    # --- 核心：Google Maps 跳转逻辑 ---
    # 构造搜索词：房源名 + 伦敦
    map_query = f"{item['title']}, London".replace(" ", "+")
    map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"📅 **发布日期**: {item['date']}")
    with col_t2:
        # 极简样式的地图按钮
        st.markdown(f'''
            <a href="{map_url}" target="_blank" style="text-decoration:none;">
                <button style="width:100%; height:32px; border-radius:6px; border:1px solid #ff4b4b; background:white; color:#ff4b4b; font-size:12px; font-weight:bold; cursor:pointer;">
                    📍 地图找房
                </button>
            </a>
        ''', unsafe_allow_html=True)

    st.markdown("### 📋 房源亮点")
    st.write(item['description'])
    st.divider()
    
    # 联系人配置
    wechat_id = "HaoHarbour_UK"
    phone_num = "447450912493" 
    
    st.markdown("💬 **立即咨询**")
    
    # 微信复制区
    with st.container(border=True):
        st.markdown(f"✨ **微信 ID (点击即可复制):**")
        st.code(wechat_id, language=None)
        st.caption("复制后在微信搜索添加即可")

    # WhatsApp & 拨号 (并排按钮)
    c1, c2 = st.columns(2)
    with c1:
        wa_url = f"https://wa.me/{phone_num}?text=您好，咨询房源：{item['title']}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; border:none; background:#25D366; color:white; font-weight:bold; cursor:pointer; width:100%;">WhatsApp</button></a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a href="tel:+{phone_num}"><button style="width:100%; height:45px; border-radius:10px; border:1px solid #25D366; background:white; color:#25D366; font-weight:bold; cursor:pointer; width:100%;">📞 拨号</button></a>', unsafe_allow_html=True)

    st.divider()

    # 海报下载
    try:
        img_data = requests.get(item['poster-link']).content
        st.download_button(label="🖼️ 下载精美海报", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except:
        pass

# --- 4. 后续逻辑保持不变 (数据加载、Header、列表展示等) ---
# (为了篇幅，以下省略部分重复逻辑，请确保在你的完整代码中保留获取数据和渲染列表的部分)
# ... (此处接你原先代码的 Header 渲染、数据获取和网格展示部分) ...
