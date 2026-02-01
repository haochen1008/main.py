import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import urllib.parse
import requests
from io import BytesIO

# --- 1. 奢华 UI 与 样式配置 (全功能保留) ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 导航标签 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 60px; font-size: 16px; color: #888 !important; }
    .stTabs [aria-selected="true"] { color: #bfa064 !important; border-bottom: 2px solid #bfa064 !important; }

    /* 服务卡片样式 */
    .service-card {
        background: #fdfcf9; border-left: 5px solid #bfa064;
        padding: 25px; border-radius: 8px; margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .service-title { color: #1a1a1a; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    
    /* 详情页排版：确保 ✓ 换行点 */
    .description-box {
        background-color: #f9f9f9; padding: 20px; border-radius: 12px;
        line-height: 2.0; font-size: 15px; color: #333;
        white-space: pre-wrap; border: 1px solid #eee; margin-bottom: 15px;
    }

    .prop-title { font-weight: bold; font-size: 19px; color: #1a1a1a; margin: 5px 0; }
    .prop-price { color: #bfa064; font-size: 23px; font-weight: bold; }
    .prop-date { font-size: 12px; color: #999; margin-bottom: 10px; }
    
    .wa-link { background-color: #25D366 !important; color: white !important; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; text-decoration: none; display: block; }
    
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据库安全连接 ---
def get_data():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(creds)
        ws = gc.open("Hao_Harbour_DB").get_worksheet(0)
        return pd.DataFrame(ws.get_all_records()), ws
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame(), None

# --- 3. 详情弹窗 (修复重复显示问题) ---
@st.dialog("Property Details")
def show_details(item, ws, row_idx):
    # A. 高清海报与下载 (F列)
    img_url = item.get('poster-link', '')
    if img_url:
        st.image(img_url, use_container_width=True)
        try:
            resp = requests.get(img_url, timeout=10)
            st.download_button(label="📥 保存高清海报到相册", data=resp.content, file_name=f"HaoHarbour_{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
        except: pass

    # B. 基本信息与日期
    st.markdown(f"## {item['title']}")
    st.markdown(f"📅 **发布日期**: {item.get('date', '近期')}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("月租", f"£{item['price']}")
    c2.metric("区域", item['region'])
    c3.metric("户型", item['rooms'])
    
    # C. 精美排版展示 (解决重复问题：仅展示)
    st.markdown("### 📜 房源亮点")
    raw_desc = str(item.get('description', ''))
    # 核心：确保 ✓ 符号前有换行符，实现每个 tick 占一行
    formatted_desc = raw_desc.replace('✓', '\n✓').strip()
    st.markdown(f'<div class="description-box">{formatted_desc}</div>', unsafe_allow_html=True)
    
    # D. 专用一键复制区 (st.code 仅保留在下方)
    st.info("💡 点击下方框内右上角即可一键复制完整文案：")
    st.code(formatted_desc, language=None)

    st.markdown("---")
    m_q = urllib.parse.quote(item['title'] + " London")
    st.link_button("📍 在 Google Maps 查看位置", f"https://www.google.com/maps/search/{m_q}", use_container_width=True)

    st.markdown("### 📱 预约看房")
    col_lh, col_rh = st.columns(2)
    with col_lh:
        st.markdown('<div style="background:#f8f9fa;padding:10px;text-align:center;border:1px solid #eee;border-radius:10px;"><b>微信咨询: HaoHarbour</b></div>', unsafe_allow_html=True)
    with col_rh:
        wa_url = f"https://wa.me/447450912493?text=Interested in {item['title']}"
        st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp</a>', unsafe_allow_html=True)

    # E. 浏览量更新 (H列)
    try:
        new_v = int(item.get('views', 0)) + 1
        ws.update_cell(row_idx, 8, new_v)
    except: pass

# --- 4. 主程序渲染 (全功能 Tabs) ---
st.markdown("<h1 style='text-align:center; color:#1a1a1a; font-family:serif; font-size:45px;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; letter-spacing:4px; font-size:12px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

df, worksheet = get_data()

if not df.empty:
    tabs = st.tabs(["🏠 房源精选", "🛠️ 专业服务", "👤 团队背景", "📞 立即咨询"])
    
    # --- TAB 1: 房源精选 ---
    with tabs[0]:
        st.warning("💡 获取最新完整房源列表，请添加微信：HaoHarbour")
        with st.expander("🔍 筛选与搜索房源", expanded=False):
            search_query = st.text_input("输入关键词搜索 (楼盘名、地铁站)...", "").lower()
            f1, f2, f3 = st.columns(3)
            sel_reg = f1.multiselect("区域", options=sorted(df['region'].unique()))
            sel_room = f2.multiselect("户型", options=sorted(df['rooms'].unique()))
            max_price = f3.slider("预算上限 (£)", 1000, 15000, 15000)
        
        f_df = df.copy()
        if search_query:
            f_df = f_df[f_df['title'].str.lower().str.contains(search_query) | f_df['description'].str.lower().str.contains(search_query)]
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df['p_num'] = pd.to_numeric(f_df['price'], errors='coerce').fillna(0)
        f_df = f_df[f_df['p_num'] <= max_price]
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

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

    # --- TAB 2: 专业服务 (补回)
