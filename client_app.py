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

with tabs[0]:
    # 把你原来的“筛选器 (Filter)”和“房源循环展示 (for loop)”代码全部放在这个 with 块下面
    st.warning("💡 由于房源众多，无法全部展示，更多伦敦优质房源，请咨询微信：HaoHarbour")
    # ... (这里放你原本的 Filter 和房源展示代码)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=300).dropna(how='all')
    
    with st.expander("🔍 Filter Options"):
        f1, f2 = st.columns(2)
        sel_reg = f1.multiselect("Region", options=df['region'].unique().tolist())
        sel_room = f2.multiselect("Rooms", options=df['rooms'].unique().tolist())
        max_p = st.slider("Max Price", 1000, 15000, 15000)

    f_df = df.copy()
    if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
    if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
    f_df = f_df[f_df['price'].fillna(0) <= max_p]
    f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

    # 展示房源卡片
 # 1. 确保这一行在 try 模块内，且左边有 4 个空格
    cols = st.columns(3)
    
    # 2. 整个循环块
    for i, (idx, row) in enumerate(f_df.iterrows()):
        with cols[i % 3]:
            # 创建一个相对定位容器，用于放置“精选”标签
            st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
            
            # --- 精选标签逻辑 ---
            # 检查 is_featured 是否为 1 或 True
            is_feat = row.get('is_featured')
            if is_feat == 1 or str(is_feat).lower() == 'true':
                st.markdown("""
                    <div style="
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background-color: #ff4b4b;
                        color: white;
                        padding: 4px 12px;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                        z-index: 10;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    ">🌟 精选房源</div>
                """, unsafe_allow_html=True)

            # --- 房源卡片内容 ---
            with st.container(border=True):
                # 房源大图
                st.image(row['poster-link'], use_container_width=True)
                
                # 房源信息文字区（带间距优化）
                st.markdown(f"""
                    <div style="padding: 15px 10px 20px 10px; text-align: center;">
                        <div style="font-weight: bold; font-size: 17px; margin-bottom: 5px;">{row['title']}</div>
                        <div style="color: #bfa064; font-size: 19px; font-weight: bold; margin-bottom: 8px;">£{int(row['price'])}</div>
                        <div style="color: #777; font-size: 12px; margin-bottom: 10px;">📍 {row['region']} | {row['rooms']}</div>
                        <div style="color: #aaa; font-size: 11px; border-top: 1px solid #f0f0f0; padding-top: 10px;">
                            发布日期: {row['date']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 查看详情按钮
                if st.button("View Details", key=f"v_{idx}", use_container_width=True):
                    show_details(row)
            
            # 闭合容器
            st.markdown('</div>', unsafe_allow_html=True)

except:
    st.info("Loading properties...")

with tabs[1]:
    st.markdown("### 🛠️ 全方位英国租房管家")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.info("📍 **全英选房**\n\n深度覆盖伦敦 (London)、曼彻斯特 (Manchester)、伯明翰 (Birmingham) 等核心求学区域。
需求画像： 根据学生所在校区、预算偏好、安全系数及周边交通进行大数据筛选。")
        
        st.info("📝 **账单托管**\n\n为您处理繁琐的英国水电网、Council Tax 等账单注册，确保您拎包入住，无后顾之忧。")
    with col_s2:
        st.info("🤝 **全程陪跑**\n\n从看房、法律文书跟进到最终拿钥匙，我们提供专业且透明的中立建议。")

with tabs[2]:
    st.markdown("### 👤 为什么选择我们？")
    st.success("""
    **资深背景，专业护航**
    * **名校基因**：创始人毕业于 **UCL (伦敦大学学院)** 本硕，拥有超过 10 年英国生活经验。
    * **行业高度**：曾任职于财富 500 强顶级房地产服务公司 **JLL (仲量联行)**，深谙行业规则与市场动向。
    * **专业主义**：多年英国房产经验，累积服务数百位高净值客户，深知留学生与新移民的痛点。
    """)

with tabs[2]:
    st.markdown("### 👤 为什么选择我们？")
    st.success("""
    **资深背景，专业护航**
    * **名校基因**：创始人毕业于 **UCL (伦敦大学学院)** 本硕，拥有超过 10 年英国生活经验。
    * **行业高度**：曾任职于财富 500 强顶级房地产服务公司 **JLL (仲量联行)**，深谙行业规则与市场动向。
    * **专业主义**：多年英国房产经验，累积服务数百位高净值客户，深知留学生与新移民的痛点。
    """)

with tabs[3]:
    st.markdown("### 📞 预约您的私人顾问")
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.markdown("**微信咨询 (WeChat)**")
        st.code("HaoHarbour_UK", language=None)
    with c_c2:
        st.markdown("**WhatsApp**")
        wa_url = "https://wa.me/447000000000"
        st.markdown(f'<a href="{wa_url}" style="background-color:#25D366; color:white; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold;">🟢 点击发起对话</a>', unsafe_allow_html=True)
