import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64


# --- 1. 页面配置与 CSS 深度优化 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 导航标签美化 */
.stTabs [data-baseweb="tab-list"] {
    gap: 20px;
    justify-content: center;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    background-color: transparent !important;
    border: none !important;
    color: #888 !important;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #bfa064 !important;
    border-bottom: 2px solid #bfa064 !important;
}
    /* 解决卡片内部太挤的问题 */
    .property-info-container {
        padding: 20px 10px !important; /* 增加上下内边距 */
        text-align: center;
    }
    .prop-title { font-weight: bold; font-size: 18px; margin-bottom: 8px; }
    .prop-price { color: #bfa064; font-size: 20px; font-weight: bold; margin-bottom: 12px; }
    .prop-tags { color: #888; font-size: 13px; margin-bottom: 8px; }
    .prop-date { color: #bbb; font-size: 12px; margin-top: 10px; border-top: 1px solid #eee; padding-top: 8px; }

    /* 修复筛选栏 */
    .st-expanderHeader > div:first-child { display: none !important; }
    .st-expanderHeader {
        background-color: #1a1c23 !important;
        border: 1px solid #bfa064 !important;
        border-radius: 12px !important;
    }

    /* WhatsApp 绿色按钮 */
    .wa-link {
        background-color: #25D366 !important;
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        display: block;
        margin: 10px 0;
    }

    /* 微信 ID 容器 */
    .wechat-header {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        border: 1px solid #eee;
        border-bottom: none;
    }

    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 详情弹窗 (顺序：微信->WhatsApp->海报->信息->描述) ---
@st.dialog("Property Details")
def show_details(item):
    # 统计
    try:
        conn_v = st.connection("gsheets", type=GSheetsConnection)
        df_v = conn_v.read(worksheet="Sheet1", ttl=0)
        df_v.loc[df_v['title'] == item['title'], 'views'] += 1
        conn_v.update(worksheet="Sheet1", data=df_v)
    except: pass

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
    wa_url = f"https://wa.me/447000000000?text=Interested in {item['title']}"
    st.markdown(f'<a href="{wa_url}" class="wa-link">💬 WhatsApp Chat</a>', unsafe_allow_html=True)
    
    # 6. 下载
    st.write("---")
    try:
        img_data = urllib.request.urlopen(item['poster-link']).read()
        st.download_button("📥 Save Poster to Phone", data=img_data, file_name=f"{item['title']}.jpg", mime="image/jpeg", use_container_width=True)
    except: pass

# --- 3. 主界面 ---
st.markdown("<h1 style='text-align:center; color:#bfa064; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:12px; margin-top:0; letter-spacing:3px;'>EXCLUSIVE LONDON LIVING</p>", unsafe_allow_html=True)

# --- 导航栏设计 ---
tabs = st.tabs(["🏠 精选房源 (Properties)", "🛠️ 我们的服务 (Services)", "👤 关于我们 (About Us)", "📞 联系方式 (Contact)"])

try:
    # 1. 获取数据
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')

    # --- TAB 1: 房源展示 ---
    with tabs[0]:
        st.warning("💡 更多伦敦优质房源，请咨询微信：HaoHarbour_UK")
        
        # 筛选器部分
        with st.expander("🔍 筛选房源 (Filter Options)"):
            f1, f2 = st.columns(2)
            sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
            sel_room = f2.multiselect("Rooms", options=df['rooms'].unique().tolist())
            max_p = st.slider("Max Price", 1000, 15000, 15000)

        f_df = df.copy()
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df = f_df[f_df['price'].fillna(0) <= max_p]
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

    # --- TAB 2: 我们的服务 (Our Services) ---
    with tabs[1]:
        st.markdown("### 🛠️ 全生命周期管家式关怀")
        # 模块 1 & 2
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
            **轻松退房 (Ongoing Concierge)**
            * **设施检查**：协助查看验房报告，确保退房时押金全额退还。
            * **清洁安排**：协助安排深度退租清洁，长期合作，靠谱实惠。
            """)

    # --- TAB 3: 关于我们 (About Us) ---
    with tabs[2]:
        st.markdown("### 👤 为什么选择 Hao Harbour？")
        st.info("""
        * **【名校精英视角】** 创始人拥有 **UCL（伦敦大学学院）本硕学历**，以校友身份深切理解留学生对学区安全及环境的严苛需求。
        * **【行业巨头背景】** 曾任职于全球房产咨询五大行之一的 **JLL（仲量联行）**，引入世界级房地产专业标准与合规流程。
        * **【十载英伦深耕】** 扎根英国生活 **10余年**，提供比导航更精准的社区治安、配套及族裔分布解析。
        * **【官方战略合作】** 与众多本土管理公司建立长期稳固合作，掌握大量“独家房源”或优先配额。
        * **【金牌服务口碑】** 成功协助数百位国际留学生完成从“纸上申请”到“温馨入住”的完美过渡。
        """)

    # --- TAB 4: 联系方式 (Contact) ---
    with tabs[3]:
        st.markdown("### 📞 预约您的私人顾问")
        con_c1, con_c2 = st.columns(2)
        with con_c1:
            st.markdown("**微信咨询 (WeChat)**")
            st.code("HaoHarbour_UK", language=None)
        with con_c2:
            st.markdown("**WhatsApp**")
            st.markdown('<a href="https://wa.me/447000000000" class="wa-link">💬 点击发起对话</a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"连接数据库出错: {e}")
