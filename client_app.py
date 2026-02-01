import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import urllib.parse
import requests

# --- 1. 页面配置与 CSS ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 核心样式：统一色调与间距 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [aria-selected="true"] { color: #bfa064 !important; border-bottom: 2px solid #bfa064 !important; }

    /* 卡片基础样式 */
    .prop-title { font-weight: bold; font-size: 19px; color: #1a1a1a; margin: 5px 0; }
    .prop-price { color: #bfa064; font-size: 23px; font-weight: bold; }
    .prop-date { font-size: 12px; color: #999; margin-bottom: 10px; }
    
    .wa-link { background-color: #25D366 !important; color: white !important; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; text-decoration: none; display: block; }
    
    /* 隐藏 Streamlit 默认页眉页脚 */
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据库连接 ---
def get_data():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        ws = gspread.authorize(creds).open("Hao_Harbour_DB").get_worksheet(0)
        return pd.DataFrame(ws.get_all_records()), ws
    except:
        return pd.DataFrame(), None

# --- 3. 详情弹窗 (彻底修复内容重复问题) ---
@st.dialog("Property Details")
def show_details(item, ws, row_idx):
    # A. 图片与下载 (F列 poster-link)
    img_url = item.get('poster-link', '')
    if img_url:
        st.image(img_url, use_container_width=True)
        try:
            resp = requests.get(img_url, timeout=10)
            st.download_button(label="📥 保存高清海报", data=resp.content, file_name=f"Hao_{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
        except: pass

    st.markdown(f"## {item['title']}")
    st.markdown(f"📅 **发布日期**: {item.get('date', '近期')}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("月租", f"£{item['price']}")
    c2.metric("区域", item['region'])
    c3.metric("户型", item['rooms'])
    
    st.markdown("---")
    
    # B. 核心修复：不再使用 markdown 展示文案，直接使用 code 框展示+复制
    st.markdown("### 📜 房源亮点")
    raw_desc = str(item.get('description', ''))
    # 逻辑：确保每个 ✓ 前面都有换行，实现“每勾一行”的整洁排版
    formatted_desc = raw_desc.replace('✓', '\n✓').strip()
    
    # 直接放置带复制功能的代码框，通过 height 参数控制高度，避免页面过长
    st.info("💡 点击右侧按钮即可一键复制完整文案：")
    st.code(formatted_desc, language=None, wrap_lines=True)

    st.markdown("---")
    # C. 交互跳转
    m_q = urllib.parse.quote(item['title'] + " London")
    st.link_button("📍 在 Google Maps 查看位置", f"https://www.google.com/maps/search/{m_q}", use_container_width=True)

    st.markdown("### 📱 预约看房")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div style="background:#f8f9fa;padding:10px;text-align:center;border:1px solid #eee;border-radius:10px;"><b>微信: HaoHarbour</b></div>', unsafe_allow_html=True)
    with col_r:
        wa_url = f"https://wa.me/447450912493?text=Interested in {item['title']}"
        st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp</a>', unsafe_allow_html=True)

    # 浏览量自动+1 (H列)
    try:
        new_v = int(item.get('views', 0)) + 1
        ws.update_cell(row_idx, 8, new_v)
    except: pass

# --- 4. 主程序 (保持所有搜索/筛选功能) ---
st.markdown("<h1 style='text-align:center; color:#1a1a1a; font-size:45px;'>HAO HARBOUR</h1>", unsafe_allow_html=True)

df, worksheet = get_data()

if not df.empty:
    tabs = st.tabs(["🏠 房源精选", "🛠️ 专业服务", "👤 团队背景", "📞 立即咨询"])
    
    with tabs[0]:
        # 搜索与筛选区
        with st.expander("🔍 筛选与搜索房源", expanded=False):
            search_query = st.text_input("输入关键词搜索 (楼盘名、地铁站、描述)...", "").lower()
            f1, f2 = st.columns(2)
            sel_reg = f1.multiselect("区域", options=sorted(df['region'].unique()))
            sel_room = f2.multiselect("户型", options=sorted(df['rooms'].unique()))
        
        f_df = df.copy()
        if search_query:
            f_df = f_df[f_df['title'].str.lower().str.contains(search_query) | f_df['description'].str.lower().str.contains(search_query)]
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

        # 网格显示
        cols = st.columns(3)
        for i, (idx, row) in enumerate(f_df.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    p_url = row.get('poster-link', '')
                    if p_url: st.image(p_url, use_container_width=True)
                    st.markdown(f'<div class="prop-title">{row["title"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prop-price">£{row["price"]} /mo</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prop-date">📍 {row["region"]} | 🗓️ {row.get("date", "近期")}</div>', unsafe_allow_html=True)
                    if st.button("查看详情", key=f"btn_{idx}", use_container_width=True):
                        show_details(row, worksheet, idx + 2)

    # 补齐 Tab 2, 3, 4 的原始内容...
    with tabs[1]:
        st.markdown("### 🛠️ 我们的专业服务")
        st.write("提供从选址到退房的全流程管家式服务。")
    with tabs[2]:
        st.markdown("### 👤 团队背景")
        st.write("UCL 硕士团队，深耕伦敦 10 余年。")
    with tabs[3]:
        st.markdown("### 📞 联系我们")
        st.write("WeChat: HaoHarbour")
