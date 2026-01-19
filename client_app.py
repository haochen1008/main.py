import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置与 CSS 深度优化 ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 1. 修复筛选房源标题颜色：强制改为白色 */
/* 1. 这里的背景色换成最稳妥的深灰色 */
   .st-expander {
        background-color: #1a1c23 !important; /* 深墨黑背景 */
        border: 1px solid #bfa064 !important; /* 金色边框 */
        border-radius: 10px !important;
    }

    .st-expanderHeader p {
        color: #ffffff !important; /* 纯白文字，绝对看得见 */
        font-weight: bold !important;
    }

    /* 2. 修复温馨提示框：去掉突兀的鲜黄色，改为深色半透明 */
    div[data-testid="stNotification"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #bfa064 !important;
        border: 1px solid rgba(191, 160, 100, 0.3) !important;
        border-radius: 10px !important;
    }

    /* 3. 修复筛选器内部的标签文字（Region, Rooms等） */
    .stMultiSelect label, .stSlider label, .stMarkdown p {
        color: #d1d1d1 !important;
    }

    /* 4. 优化房源卡片下方的信息间距，解决拥挤问题 */
    .property-info-container {
        padding: 20px 15px !important;
        background: #ffffff;
        border-radius: 0 0 15px 15px;
    }

    /* 5. 保持精选标签的高亮 */
    .featured-badge {
        position: absolute;
        top: 15px;
        left: 15px;
        background: linear-gradient(45deg, #ff4b4b, #ff7675);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        z-index: 10;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* 全局背景与字体 */
    .stApp { background-color: #fcfcfc; }
    
    /* 导航栏美化 - 黄金分割感 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 40px;
        justify-content: center;
        border-bottom: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        font-size: 16px;
        color: #666 !important;
        background-color: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #bfa064 !important;
        border-bottom: 3px solid #bfa064 !important;
        font-weight: bold;
    }

    /* 高级感服务卡片 */
    .service-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #bfa064;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .service-card:hover { transform: translateY(-5px); }
    .service-title { color: #1a1c23; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .service-text { color: #555; font-size: 14px; line-height: 1.6; }

    /* 关于我们 - 履历墙样式 */
    .bio-box {
        background: linear-gradient(135deg, #1a1c23 0%, #343a40 100%);
        color: #f1f1f1;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #bfa064;
    }
    .bio-tag {
        display: inline-block;
        background: rgba(191, 160, 100, 0.2);
        color: #bfa064;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin-bottom: 10px;
        border: 1px solid #bfa064;
    }

/* 1. 彻底移除顶部状态栏（包含 GitHub 和 Manage App 入口） */
    header, [data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        visibility: hidden !important;
    }

    /* 2. 彻底移除底部 Streamlit 标志 */
    footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 3. 针对手机端右下角“三个点”菜单和悬浮球的暴力隐藏 */
    [data-testid="stStatusWidget"], 
    .stAppDeployButton, 
    #MainMenu, 
    [data-testid="stToolbar"],
    [data-testid="stManageAppButton"],
    #viewerBadge {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* 4. 移除移动端特有的交互栏 */
    div[data-testid="stHeader"] ~ div {
        --st-header-height: 0px !important;
    }

    /* 精选标签样式 */
    .featured-badge {
        position: absolute;
        top: 15px;
        left: 15px;
        background: linear-gradient(45deg, #ff4b4b, #ff7675);
        color: white;
        padding: 5px 15px;
        border-radius: 30px;
        font-size: 11px;
        font-weight: bold;
        z-index: 10;
        box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
    }
    /* 1. 隐藏手机端右下角的管理悬浮球 (Manage App button) */
#viewerBadge, .viewerBadge_container__17768, [data-testid="stManageAppButton"] {
    display: none !important;
    }

    /* 1. 强制溢出屏蔽：从根源上切断任何超出页面的组件显示 */
    .stApp {
        overflow: hidden !important;
    }

    /* 2. 深度清理 Header 和 Footer */
    [data-testid="stHeader"], 
    header, 
    footer, 
    [data-testid="stFooter"] {
        display: none !important;
        height: 0px !important;
        max-height: 0px !important;
        margin: 0 !important;
        padding: 0 !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    /* 3. 手机端右下角三个点菜单、Manage App、Deploy 全面封杀 */
    [data-testid="stStatusWidget"],
    [data-testid="stToolbar"],
    [data-testid="stManageAppButton"],
    #viewerBadge,
    .stAppDeployButton,
    button[kind="headerNoPadding"],
    div[class*="viewerBadge"],
    div[class*="StyledStatusWidget"] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* 4. 针对手机端交互栏的强制补丁 */
    div[class*="stAppViewMain"] {
        margin-top: -50px !important; /* 向上顶出屏幕范围 */
    }
    
    /* 彻底隐藏右上角的 GitHub 图标、Deploy 按钮和三道杠菜单 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 针对 Streamlit 2025/2026 新版界面的强制隐藏逻辑 */
.stAppDeployButton {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
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
    st.code("HaoHarbour_UK", language=None)
    
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
        # --- 核心修改：给筛选区域加一个背景色，让白字能看见 ---
        st.markdown("""
            <style>
                /* 1. 将整个筛选器容器设为深灰色背景 */
                .st-expander {
                    background-color: #2c2f33 !important;
                    border: 1px solid #bfa064 !important;
                    border-radius: 12px !important;
                }
                
                /* 2. 确保标题文字是纯白色 */
                .st-expanderHeader p {
                    color: #ffffff !important;
                    font-size: 16px !important;
                    font-weight: bold !important;
                }

                /* 3. 内部选项文字也设为白色 */
                .stMultiSelect label, .stSlider label {
                    color: #ffffff !important;
                }
                
                /* 4. 修改下拉框内的文字颜色，防止看不见 */
                div[data-baseweb="select"] {
                    color: #1a1c23 !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # 这里的提示框保持现在的金棕色风格
        #st.markdown('<div class="custom-warning">💡 温馨提示：更多伦敦优质房源，请咨询微信：HaoHarbour_UK</div>', unsafe_allow_html=True)
        

        
        st.markdown("""
            <style>
                /* 修复筛选器标题颜色：改为深灰色/金色 */
                .st-expanderHeader p, .st-expanderHeader span {
                    color: #1a1c23 !important;
                    font-weight: bold !important;
                    font-size: 16px !important;
                }
                
                /* 修复筛选器图标颜色 */
                .st-expanderHeader svg {
                    fill: #bfa064 !important;
                }

                /* 修复表单内部文字颜色 */
                .stMultiSelect label, .stSlider label {
                    color: #444444 !important;
                    font-weight: 500 !important;
                }

                /* 温馨提示框：改为更高级的淡金色背景 */
                .custom-warning {
                    background-color: #fff9eb !important;
                    color: #856404 !important;
                    padding: 20px;
                    border: 1px solid #ffeeba;
                    border-radius: 12px;
                    margin-bottom: 25px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }

                /* 房源卡片内部文字 */
                .prop-title { font-weight: bold; color: #1a1c23; font-size: 1.1em; }
                .prop-price { color: #bfa064; font-size: 1.2em; font-weight: bold; margin: 5px 0; }
                .prop-tags { color: #666; font-size: 0.9em; }
            </style>
            
            <div class="custom-warning">
                💡 <b>温馨提示：</b> 由于房源数量众多，网站仅展示部分精选房源。<br>
                如需了解更多伦敦优质房源，请添加微信：<b>HaoHarbour_UK</b> 咨询。
            </div>
        """, unsafe_allow_html=True)

        # 2. 筛选器部分
        with st.expander("🔍 筛选房源 (Filter Options)"):
            f1, f2 = st.columns(2)
            # 确保数据加载正常
            sel_reg = f1.multiselect("选择区域 (Region)", options=df['region'].unique().tolist())
            sel_room = f2.multiselect("房型 (Rooms)", options=df['rooms'].unique().tolist())
            max_p = st.slider("最高预算 (Max Price £/pcm)", 1000, 15000, 15000)

        # 3. 房源逻辑与展示 (确保此处缩进正确)
        f_df = df.copy()
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df = f_df[f_df['price'].fillna(0) <= max_p]
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

        # 渲染房源列表
        cols = st.columns(3)
        for i, (idx, row) in enumerate(f_df.iterrows()):
            with cols[i % 3]:
                # 外层容器增加边框
                with st.container(border=True):
                    # 1. 精选标签 (靠右显示)
                    if row.get('is_featured') == 1:
                        st.markdown('<div style="text-align:right;"><span style="background:#ff4b4b; color:white; padding:2px 8px; border-radius:4px; font-size:10px;">🌟 精选房源</span></div>', unsafe_allow_html=True)
                    
                    # 2. 房源图片
                    st.image(row['poster-link'], use_container_width=True)
                    
                    # 3. 核心信息区域：强制居中并加深日期颜色
                    st.markdown(f"""
                        <div style="text-align: center; width: 100%; padding: 10px 0;">
                            <div style="font-weight: bold; color: #1a1c23; font-size: 1.15em; margin-bottom: 6px;">
                                {row['title']}
                            </div>
                            <div style="color: #bfa064; font-size: 1.25em; font-weight: bold; margin-bottom: 6px;">
                                £{int(row['price'])} /pcm
                            </div>
                            <div style="color: #444444; font-size: 0.95em; margin-bottom: 6px;">
                                📍 {row['region']} | {row['rooms']}
                            </div>
                            <div style="color: #666666; font-size: 0.85em; font-weight: 500;">
                                发布日期: {row['date']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 4. 详情按钮
                    if st.button("查看详情 (Details)", key=f"btn_{idx}", use_container_width=True):
                        show_details(row)
                       

    # --- TAB 2, 3, 4 的逻辑保持在后面即可 ---
   # --- TAB 2: 我们的服务 ---
    with tabs[1]:
        st.markdown("<h2 style='text-align:center; color:#1a1c23;'>Bespoke Concierge Services</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888;'>全生命周期管家式关怀，让海外置业更简单</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="service-card">
                    <div class="service-title">📍 模块 1：精准定向选址</div>
                    <div class="service-text">
                        不仅是找房子，更是匹配生活方式。深度覆盖<b>伦敦、曼城、伯明翰</b>。
                        提供高清视频带看或实地考察报告，全方位展示真实状况，杜绝“买家秀”骗局。
                    </div>
                </div>
                <div class="service-card">
                    <div class="service-title">🔑 模块 3：极速入住管家</div>
                    <div class="service-text">
                        协助开通水、电、煤气及高性价比网络。指导申请 <b>Council Tax 免税证明</b>，
                        入住当天协助 Inventory 拍照存证，确保退房时押金全额退还。
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="service-card">
                    <div class="service-title">⚖️ 模块 2：文书合规与风控</div>
                    <div class="service-text">
                        利用 <b>JLL 标准</b> 的专业知识保护您的利益。协助 Reference 审查，
                        深度审计租约，确保押金受 TDS 保护，并凭借经验为您争取最优惠租金。
                    </div>
                </div>
                <div class="service-card">
                    <div class="service-title">🌟 模块 4：增值生活支持</div>
                    <div class="service-text">
                        服务不因租约签订而终止。入住期间提供漏水、设备维修等纠纷的咨询，
                        并针对下一学年的续租或迁徙提供前瞻性建议。
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # --- TAB 3: 关于我们 ---
    with tabs[2]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div class="bio-box">
                <div class="bio-tag">FOUNDER PROFILE</div>
                <h2 style='margin:0; color:#bfa064;'>Hao Harbour 创始人</h2>
                <p style='font-size:18px; opacity:0.9;'>UCL (伦敦大学学院) 本硕 | 前 JLL (仲量联行) 顾问</p>
                <hr style='opacity:0.2; margin:20px 0;'>
                <p style='line-height:1.8; font-size:15px;'>
                    🌟 <b>名校精英视角</b>：以校友身份深切理解留学生对学区安全与通勤的严苛需求。<br>
                    🏢 <b>行业巨头背景</b>：曾任职于五大行之一的 JLL，引入世界级房地产专业标准。<br>
                    🇬🇧 <b>十载英伦深耕</b>：扎根英国 10 余年，提供比地图更精准的社区治安及族裔分布解析。<br>
                    🤝 <b>官方战略合作</b>：与众多本土管理公司建立稳固合作，掌握大量不公开的“独家房源”。<br>
                    🏆 <b>金牌服务口碑</b>：成功协助数百位留学生完成从申请到入住的完美过渡。
                </p>
            </div>
        """, unsafe_allow_html=True)

    # --- TAB 4: 联系方式 (Contact) ---
   # --- TAB 4: 联系方式 (Contact) ---
    with tabs[3]:
        # 引用 GitHub 仓库中的图片（请确保路径正确）
        qr_url = "wechat_qr.png" 
        
        st.markdown("<h2 style='text-align:center; color:#1a1c23; margin-top:20px;'>Contact Our Team</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888;'>专业顾问为您提供 1-on-1 中英双语置业咨询</p>", unsafe_allow_html=True)
        
        # 使用列布局显示三个联系方式
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("""
                <div style="text-align: center; padding: 20px; background: white; border-radius: 15px; border: 1px solid #e0e0e0; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3670/3670325.png" width="50" style="margin-bottom:10px;">
                    <h4 style="margin:0; color:#1a1c23;">WeChat</h4>
                    <p style="color:#bfa064; font-weight:bold; margin:5px 0;">HaoHarbour_UK</p>
                    <p style="font-size:12px; color:#999;">扫码或添加微信号咨询</p>
                </div>
            """, unsafe_allow_html=True)
            # 加载你 GitHub 里的二维码
            st.image(qr_url, caption="扫一扫添加微信", use_container_width=True)

        with c2:
            st.markdown("""
                <div style="text-align: center; padding: 20px; background: white; border-radius: 15px; border: 1px solid #e0e0e0; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3670/3670051.png" width="50" style="margin-bottom:10px;">
                    <h4 style="margin:0; color:#1a1c23;">WhatsApp</h4>
                    <p style="color:#25D366; font-weight:bold; margin:5px 0;">+44 7450 912493</p>
                    <a href="https://wa.me/447450912493" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#25D366; color:white; padding:10px 20px; border-radius:25px; font-weight:bold; margin-top:10px;">立即交谈</div>
                    </a>
                </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown("""
                <div style="text-align: center; padding: 20px; background: white; border-radius: 15px; border: 1px solid #e0e0e0; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/3059/3059590.png" width="50" style="margin-bottom:10px;">
                    <h4 style="margin:0; color:#1a1c23;">Phone</h4>
                    <p style="color:#bfa064; font-weight:bold; margin:5px 0;">07450912493</p>
                    <a href="tel:07450912493" style="text-decoration:none;">
                        <div style="background-color:#1a1c23; color:white; padding:10px 20px; border-radius:25px; font-weight:bold; margin-top:10px;">拨打电话</div>
                    </a>
                </div>
            """, unsafe_allow_html=True)
            
except Exception as e:
    st.error(f"连接数据库出错: {e}")
