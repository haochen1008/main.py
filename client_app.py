import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import urllib.parse
import requests
from io import BytesIO

# --- 1. 奢华 UI 与 样式配置 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 导航与标签样式 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 60px; font-size: 16px; color: #888 !important; }
    .stTabs [aria-selected="true"] { color: #bfa064 !important; border-bottom: 2px solid #bfa064 !important; }

    /* 房源详情：确保 ✓ 换行与整洁排版 */
    .description-box {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 12px;
        line-height: 2.0;
        font-size: 15px;
        color: #333;
        white-space: pre-wrap;
        border: 1px solid #eee;
    }

    .prop-title { font-weight: bold; font-size: 19px; color: #1a1a1a; margin: 5px 0; }
    .prop-price { color: #bfa064; font-size: 23px; font-weight: bold; }
    .prop-date { font-size: 12px; color: #999; margin-bottom: 10px; }
    
    /* 精选标签 */
    .featured-badge { 
        position: absolute; top: 10px; left: 10px; 
        background: rgba(191, 160, 100, 0.9); color: white; 
        padding: 4px 12px; border-radius: 4px; font-size: 11px; z-index: 10; 
    }
    
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

# --- 3. 房源详情弹窗 (含一键复制/下载/日期) ---
@st.dialog("Property Details")
def show_details(item, ws, row_idx):
    # A. 高清海报与下载 (F列)
    img_url = item.get('poster-link', '')
    if img_url:
        st.image(img_url, use_container_width=True)
        try:
            resp = requests.get(img_url, timeout=10)
            st.download_button(
                label="📥 保存高清海报到相册",
                data=resp.content,
                file_name=f"HaoHarbour_{item['title']}.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
        except:
            st.caption("暂不支持直接下载，可长按上方图片保存")

    # B. 基本信息与日期
    st.markdown(f"## {item['title']}")
    st.markdown(f"📅 **发布于**: {item.get('date', '近期')}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("月租", f"£{item['price']}")
    c2.metric("区域", item['region'])
    c3.metric("户型", item['rooms'])
    
    # C. 整洁文案排版 (自动换行)
    st.markdown("### 📜 房源亮点")
    # 强制将 ✓ 识别为换行点，确保排版整齐
    raw_desc = str(item.get('description', ''))
    formatted_desc = raw_desc.replace('✓', '\n✓').strip()
    st.markdown(f'<div class="description-box">{formatted_desc}</div>', unsafe_allow_html=True)
    
    # D. 一键复制功能
    st.write("点击下方框内右上角按钮即可一键复制文案：")
    st.code(formatted_desc, language=None)

    st.markdown("---")
    # E. 交互功能
    m_q = urllib.parse.quote(item['title'] + " London")
    st.link_button("📍 在 Google Maps 查看位置", f"https://www.google.com/maps/search/{m_q}", use_container_width=True)

    st.markdown("### 📱 预约看房")
    col_lh, col_rh = st.columns(2)
    with col_lh:
        st.markdown('<div style="background:#f8f9fa;padding:10px;text-align:center;border:1px solid #eee;border-radius:10px 10px 0 0;"><b>微信咨询</b></div>', unsafe_allow_html=True)
        st.code("HaoHarbour", language=None)
    with col_rh:
        wa_url = f"https://wa.me/447450912493?text=Interested in {item['title']}"
        st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp</a>', unsafe_allow_html=True)

    # F. 增加浏览量 (H列)
    try:
        new_v = int(item.get('views', 0)) + 1
        ws.update_cell(row_idx, 8, new_v)
    except: pass

# --- 4. 主程序渲染 ---
st.markdown("<h1 style='text-align:center; color:#1a1a1a; font-family:serif; font-size:45px;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; letter-spacing:4px; font-size:12px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

df, worksheet = get_data()

if not df.empty:
    tabs = st.tabs(["🏠 房源精选", "🛠️ 专业服务", "👤 团队背景", "📞 立即咨询"])
    
    with tabs[0]:
        st.warning("💡 获取最新完整房源列表，请添加微信：HaoHarbour")
        
        # 补回搜索与筛选功能
        with st.expander("🔍 筛选与搜索房源", expanded=False):
            search_query = st.text_input("输入关键词搜索 (如楼盘名、地铁站)...", "").lower()
            f1, f2, f3 = st.columns(3)
            sel_reg = f1.multiselect("区域", options=sorted(df['region'].unique()))
            sel_room = f2.multiselect("户型", options=sorted(df['rooms'].unique()))
            max_price = f3.slider("预算上限 (£)", 1000, 15000, 15000)
        
        # 应用过滤逻辑
        f_df = df.copy()
        if search_query:
            f_df = f_df[f_df['title'].str.lower().str.contains(search_query) | 
                        f_df['description'].str.lower().str.contains(search_query)]
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df['price_num'] = pd.to_numeric(f_df['price'], errors='coerce').fillna(0)
        f_df = f_df[f_df['price_num'] <= max_price]
        
        # 排序：精选优先，日期倒序
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

        # 房源网格显示
        cols = st.columns(3)
        for i, (idx, row) in enumerate(f_df.iterrows()):
            with cols[i % 3]:
                st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
                if str(row.get('is_featured')) == '1':
                    st.markdown('<div class="featured-badge">PREMIUM 精选</div>', unsafe_allow_html=True)
                
                with st.container(border=True):
                    p_url = row.get('poster-link', '')
                    if p_url: st.image(p_url, use_container_width=True)
                    
                    st.markdown(f'<div class="prop-title">{row["title"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prop-price">£{row["price"]} /mo</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="prop-date">📍 {row["region"]} | 🗓️ {row.get("date", "近期")}</div>', unsafe_allow_html=True)
                    
                    if st.button("查看详情", key=f"btn_{idx}", use_container_width=True):
                        show_details(row, worksheet, idx + 2)
                st.markdown('</div>', unsafe_allow_html=True)

    # 保留其他 Tabs 功能（专业服务、团队、联系方式）
    with tabs[1]:
        st.markdown("### 🛠️ 全生命周期管家服务")
        st.info("从精准选址到合同审计，从账单代缴到退房保障，我们提供英国一站式租赁解决方案。")
    with tabs[2]:
        st.markdown("### 👤 团队背景")
        st.success("UCL 硕士团队，深耕伦敦 10 余年，曾任职 JLL 等顶尖房产咨询机构。")
    with tabs[3]:
        st.markdown("### 📞 联系我们")
        st.write("微信：**HaoHarbour**")
