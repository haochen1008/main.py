import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import urllib.parse
import base64
import urllib.request

# --- 1. 核心认证与数据连接 (仅修复底层，不改动文案) ---
def get_data_from_gs():
    try:
        info = dict(st.secrets["gcp_service_account"])
        # 物理拼装私钥，确保格式绝对正确
        key_parts = ["MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCRayoKdXw38HlF", "6J23Bbyq7zAzCWQ5OAtzk0/fOhbnFUHJTMOF1njbBw92x9etYoDt5WbBUwbexaQE", "6mTmvNU0pIGEH+iUWxvkb0VNWe3o1AceLLyDECR8p+srO04Un9hP9N0k+3SzNUFo", "xTSQCMg+GVDLJN2TLTZ3MaAuJY+UtZ+tk0K01PMZGRGu8Jl0iSZhlsbZeTSptzMJ", "UIZRnbIu8HVGVfZYGWEb1sWmUBMKsJAkr5nWPDCTgQex98rdrgSKNxT+I8x6nQMz", "pkqVTcAOlShz8bXr85C/g+t8wFMSFZKi0KGdweZY1pgTkRe7589V/ne4omfK0oqu", "q7BLqPYtAgMBAAECgf9yRxG3eT+Az4zYsAWlrSuOeY9l/67YwQF2CB/3nDAprTQ+", "QAxnf2HIUA4mEdTysdwMO1ptOvuiY8DOZ2paAtvzjg2ypW/PqSQd4e9R25K4PxT5", "h0UvZO1bpLOOCFwWgVAcEjKZ1MEmIzonCN0Kx22aqtRmJblpc4uwgcZ53MHmN1qH", "UoSB1zw9c6EEoevxDAlve7yuVE5BU0kHtyaQANTShDjbLMFt2yvRBY4ZSuqJVjKG", "BWt6gTPyTHm3JcMxNOkEaxT/4eJytU1GUuqxShQf4rRCfeaCCcBPnzWl9LigYQ1O", "+s3b6rxjioi2p+nzgzhVpQVnaa7eGxojoaNpkukCgYEAwytmFQ1oLK+EzET6u2Bt", "O/qB2sxn3iKFaHMRBF2HEAOmmwCxqipvswiQmrV2pX1t+TQd+kk5z6iEpgsmm9HY", "mdUv9QBN23TmOfS1UJjLkeKmRfanhr700QpwW29yuL/RBpvSanXDnreiFw5gMT+/", "/AODyVyKDzPUwleamZtsvrUCgYEAvr4iMO8B9u6j4EPVa8XKl2ho2tm9qgrviIbd", "dvu4itmgECC/BWEsvJhgoqm1jG8A+KMhf5oUZJKrwMB0EjOM+r43PzjYfY+CvtAz", "Mfea+rbhCWootwt9YWeqkBay00jtVe0kKMcaXzfcNUucDRDa8+8RLhUunBx6SzGj", "BW3gjJkCgYB4ZpeNOT4hAw6brZo4ah45OCtPvXX+VbGTZBkFZmVh/b6UNPNllNRf", "0FLU/kl5gk2LxRkRRIdDkiRzAsIIsoY7MIdrT4q4bf9xlYMde4VqNDZ7RtTGjZse", "MqBp5/EQBFWBDDPctVW+3m5CZv30o+1eHRT57frFsiX41m5rgLSvWQKBgDvGZfyj", "yh/SZXTQjT96+qQ8Si/bcL6rMqm8agbxl8GbtbeYK4TKETUBI7eWK5jY6JsCtGrC", "pIVoGX8MUNOraBDkL3gWnnGq2bRmlsSf7eeIDDnhFOVYKnCuBhuloWDpR8dXy68j", "xjX00YO6MCtADv3G+8FPTg4KNqD96zK2XlpxAoGAWxLPxsJM71wnUXloar4X1pZU", "H5sKI9x0ivkug/DwaDbXZP4CO5f09L1yvQhXN1hQVqBKENXFOKgT1ZkKc5aIo+Py", "8GkcvwcQLsXUrli1JW0dbTUYYFH+lbvB7Kpn78Lxgdwv0vYFbTjAeW1Pgyzq9G97", "6FI0qUia8eWEUNibK1k="]
        info["private_key"] = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(key_parts) + "\n-----END PRIVATE KEY-----"
        creds = service_account.Credentials.from_service_account_info(info)
        gc = gspread.authorize(creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
        ws = gc.open("Hao_Harbour_DB").get_worksheet(0)
        return pd.DataFrame(ws.get_all_records())
    except Exception as e:
        st.error(f"连接数据库出错: {e}")
        return pd.DataFrame()

# --- 2. 页面配置与 CSS 深度优化 (还原你的原始样式) ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 导航标签美化 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent !important; border: none !important; color: #888 !important; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #bfa064 !important; border-bottom: 2px solid #bfa064 !important; }
    /* 解决卡片内部太挤的问题 */
    .property-info-container { padding: 20px 10px !important; text-align: center; }
    .prop-title { font-weight: bold; font-size: 18px; margin-bottom: 8px; }
    .prop-price { color: #bfa064; font-size: 20px; font-weight: bold; margin-bottom: 12px; }
    .prop-tags { color: #888; font-size: 13px; margin-bottom: 8px; }
    .prop-date { color: #bbb; font-size: 12px; margin-top: 10px; border-top: 1px solid #eee; padding-top: 8px; }
    .featured-badge { position: absolute; top: 10px; left: 10px; background: rgba(191,160,100,0.9); color: white; padding: 4px 12px; border-radius: 20px; z-index: 10; font-size: 12px; }
    /* 修复筛选栏 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader { background-color: #1a1c23 !important; border: 1px solid #bfa064 !important; border-radius: 12px !important; }
    /* WhatsApp 绿色按钮 */
    .wa-link { background-color: #25D366 !important; color: white !important; text-align: center; padding: 12px; border-radius: 10px; font-weight: bold; text-decoration: none; display: block; margin: 10px 0; }
    /* 微信 ID 容器 */
    .wechat-header { background-color: #f8f9fa; padding: 10px; border-radius: 10px 10px 0 0; text-align: center; border: 1px solid #eee; border-bottom: none; }
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 3. 详情弹窗 (还原你的原始顺序) ---
@st.dialog("Property Details")
def show_details(item):
    # 3. 房源海报
    st.image(item['poster-link'], use_container_width=True)
    
    # 4. 标题与地图
    c_t, c_m = st.columns([2, 1])
    with c_t:
        st.markdown(f"### {item['title']}")
        st.markdown(f"<h4 style='color:#bfa064; margin-top:-10px;'>£{item['price']}</h4>", unsafe_allow_html=True)
    with c_m:
        m_q = urllib.parse.quote(item['title'] + " London")
        st.link_button("📍 Open Map", f"https://www.google.com/maps/search/?api=1&query={m_q}", use_container_width=True)

    # 5. 描述
    st.markdown("---")
    st.markdown("📜 **Description (Click to Copy)**")
    st.code(item.get('description', 'No info'), language=None)

    # 1. 微信 (置顶)
    st.markdown('<div class="wechat-header"><b>微信咨询 (WeChat):</b></div>', unsafe_allow_html=True)
    st.code("HaoHarbour", language=None)
    
    # 2. WhatsApp
    wa_url = f"https://wa.me/447450912493?text=Interested in {item['title']}"
    st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp Chat</a>', unsafe_allow_html=True)
    
    # 6. 下载
    st.write("---")
    try:
        img_data = urllib.request.urlopen(item['poster-link']).read()
        st.download_button("📥 Save Poster to Phone", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: pass

# --- 4. 主界面 ---
st.markdown("<h1 style='text-align:center; color:#bfa064; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:12px; margin-top:0; letter-spacing:3px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

# --- 导航栏设计 ---
tabs = st.tabs(["🏠 精选房源 (Properties)", "🛠️ 我们的服务 (Services)", "👤 关于我们 (About Us)", "📞 联系方式 (Contact)"])

# 1. 获取数据
df = get_data_from_gs()

if not df.empty:
    # --- TAB 1: 房源展示 ---
    with tabs[0]:
        st.warning("💡 温馨提示：由于房源众多无法全部展示，更多优质房源，请咨询微信：HaoHarbour")
        
        # 筛选器部分
        with st.expander("🔍 筛选房源 (Filter Options)"):
            f1, f2 = st.columns(2)
            sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
            sel_room = f2.multiselect("Rooms", options=df['rooms'].unique().tolist())
            max_p = st.slider("Max Price", 1000, 15000, 15000)

        f_df = df.copy()
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df['price'] = pd.to_numeric(f_df['price'], errors='coerce').fillna(0)
        f_df = f_df[f_df['price'] <= max_p]
        # 确保精选房源置顶
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

        cols = st.columns(3)
        for i, (idx, row) in enumerate(f_df.iterrows()):
            with cols[i % 3]:
                st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
                # 精选标签渲染
                if row.get('is_featured') == 1:
                    st.markdown('<div class="featured-badge">🌟 精选房源</div>', unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.image(row['poster-link'], use_container_width=True)
                    # 间距优化排版
                    st.markdown(f"""
                        <div class="property-info-container">
                            <div class="prop-title">{row['title']}</div>
                            <div class="prop-price">£{int(row['price'])}</div>
                            <div class="prop-tags">📍 {row['region']} | {row['rooms']}</div>
                            <div class="prop-date">发布日期: {row['date']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("View Details", key=f"v_{idx}", use_container_width=True):
                        show_details(row)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: 我们的服务 (还原原始文案) ---
    with tabs[1]:
        st.markdown("### 🛠️ 全生命周期管家式关怀")
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            st.markdown("""
            **精准定向选址 (Bespoke Property Search)**
            * **覆盖城市**：深度覆盖伦敦、曼彻斯特、伯明翰等核心求学区域。
            * **需求画像**：根据校区、预算、安全系数及周边交通进行大数据筛选。
            """)
            st.markdown("""
            **账单管家 (Utility Setting-up Support)**
            * **Utilities 托管**：协助开通水、电、煤气及高性价比宽带网络运营商。
            * **政务处理**：指导申请 Council Tax 免税证明，节省高额开支。
            """)
        with s_c2:
            st.markdown("""
            **文书合规与风控 (Contract & Compliance)**
            * **租房审查协助**：针对留学生无英国担保人痛点提供专业指导。
            * **合同审计**：深度解读 Tenancy Agreement，确保押金受 TDS 保护。
            """)
            st.markdown("""
            **轻松退房 (Easy Check Out)**
            * **设施检查**：协助查看验房报告，确保退房时押金全额退还。
            * **清洁安排**：协助安排深度退租清洁，长期合作，靠谱实惠。
            """)

    # --- TAB 3: 关于我们 (还原原始文案) ---
    with tabs[2]:
        st.markdown("### 👤 为什么选择 Hao Harbour？")
        st.info("""
        * **【名校精英视角】** 创始人拥有 **UCL（伦敦大学学院）本硕学历**，以校友身份深切理解留学生对学区安全及环境的严苛需求。
        * **【行业巨头背景】** 曾任职于全球房产咨询五大行之一，财富500强公司的 **JLL（仲量联行）**，引入世界级房地产专业标准与合规流程。
        * **【十载英伦深耕】** 扎根英国生活 **10余年**，提供比导航更精准的社区治安、配套及族裔分布解析。
        * **【官方战略合作】** 与众多本土管理公司建立长期稳固合作，掌握大量“独家房源”或优先配额。
        * **【金牌服务口碑】** ARLA专业持牌地产专家，成功协助数百位国际留学生完成从“纸上申请”到“温馨入住”的完美过渡。
        """)

    # --- TAB 4: 联系方式 (还原原始内容) ---
    with tabs[3]:
        st.markdown("### 📞 预约您的私人顾问")
        con_c1, con_c2 = st.columns(2)
        with con_c1:
            st.markdown("**微信咨询 (WeChat)**")
            st.code("HaoHarbour", language=None)
        with con_c2:
            st.markdown("**WhatsApp**")
            st.markdown('<a href="https://wa.me/447450912493" class="wa-link">💬 点击发起对话</a>', unsafe_allow_html=True)
else:
    st.info("正在加载房源数据，请稍候... 若长时间未出现，请检查 Secrets 设置。")
