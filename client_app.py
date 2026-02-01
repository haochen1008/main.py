import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import urllib.parse
import base64

# --- 1. 页面配置 (保持原有的奢华感 CSS) ---
st.set_page_config(page_title="Hao Harbour | London Luxury", layout="wide")

st.markdown("""
    <style>
    /* 导航标签 */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 60px; font-size: 16px; color: #888 !important; }
    .stTabs [aria-selected="true"] { color: #bfa064 !important; border-bottom: 2px solid #bfa064 !important; }

    /* 服务卡片样式 */
    .service-card {
        background: #fdfcf9;
        border-left: 5px solid #bfa064;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .service-title { color: #1a1a1a; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    
    /* 团队背景深色卡片 */
    .bio-box {
        background: #1a1c23;
        color: white;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #bfa064;
    }
    .highlight-gold { color: #bfa064; font-weight: bold; }
    
    /* 房源卡片样式 */
    .property-info-container { padding: 15px 10px; text-align: center; }
    .prop-title { font-weight: bold; font-size: 18px; color: #333; }
    .prop-price { color: #bfa064; font-size: 22px; font-weight: bold; margin: 8px 0; }
    .featured-badge { position: absolute; top: 10px; left: 10px; background: #bfa064; color: white; padding: 4px 15px; border-radius: 20px; font-size: 12px; z-index: 10; }
    
    .wa-link { background-color: #25D366 !important; color: white !important; text-align: center; padding: 15px; border-radius: 10px; font-weight: bold; text-decoration: none; display: block; }
    .wechat-header { background-color: #f8f9fa; padding: 10px; border-radius: 10px 10px 0 0; text-align: center; border: 1px solid #eee; border-bottom: none; }
    
    #MainMenu, footer, .stAppDeployButton, [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心数据连接 ---
def get_data_from_gs():
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
        # 获取所有数据
        data = ws.get_all_records()
        return pd.DataFrame(data), ws
    except Exception as e:
        st.error(f"⚠️ 数据库连接失败: {e}")
        return pd.DataFrame(), None

# --- 3. 详情弹窗函数 (兼容图片读取与流量统计) ---
@st.dialog("Property Details")
def show_details(item, ws, row_idx):
    # 核心修复：从 F 列读取图片（在 records 转换后的 dict 中 key 为 'poster-link'）
    img_val = item.get('poster-link', '')
    
    # 兼容性检测：支持 Cloudinary URL 和 旧的 Base64
    if isinstance(img_val, str) and (img_val.startswith("http") or img_val.startswith("data:image")):
        st.image(img_val, use_container_width=True)
    else:
        st.warning("📷 房源预览图加载中或暂无预览")

    st.markdown(f"## {item['title']}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("月租金", f"£{item['price']}")
    c2.metric("区域", item['region'])
    c3.metric("户型", item['rooms'])
    
    st.markdown("---")
    # Google Maps 跳转逻辑
    m_q = urllib.parse.quote(item['title'] + " London")
    st.link_button("📍 在 Google Maps 查看位置", f"https://www.google.com/maps/search/?api=1&query={m_q}", use_container_width=True)

    st.markdown("### 📜 房源亮点")
    st.info(item.get('description', '暂无详细描述'))
    
    st.markdown("---")
    st.markdown("### 📱 预约看房")
    col_lh, col_rh = st.columns(2)
    with col_lh:
        st.markdown('<div class="wechat-header"><b>微信咨询 (WeChat)</b></div>', unsafe_allow_html=True)
        st.code("HaoHarbour", language=None)
    with col_rh:
        wa_url = f"https://wa.me/447450912493?text=Interested in {item['title']}"
        st.markdown(f'<a href="{wa_url}" class="wa-link" style="padding: 11px;">💬 WhatsApp</a>', unsafe_allow_html=True)

    # 浏览量自动更新逻辑
    try:
        # 假设 views 在 H 列（第 8 列）
        current_views = 0
        try:
            current_views = int(item.get('views', 0))
        except: pass
        ws.update_cell(row_idx, 8, current_views + 1)
    except:
        pass

# --- 4. 主界面渲染 ---
st.markdown("<h1 style='text-align:center; color:#1a1a1a; font-family:serif; font-size:45px; margin-bottom:0;'>HAO HARBOUR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#bfa064; font-size:14px; margin-top:0; letter-spacing:5px; text-transform:uppercase;'>Exclusive London Living</p>", unsafe_allow_html=True)

df, worksheet = get_data_from_gs()

tabs = st.tabs(["🏠 房源精选", "🛠️ 专业服务", "👤 团队背景", "📞 立即咨询"])

# --- TAB 1: 房源展示 ---
with tabs[0]:
    if not df.empty:
        st.warning("💡 由于房源更新极快，网页仅展示部分精选。获取最新完整房源列表，请微信HaoHarbour。")
        
        with st.expander("🔍 筛选理想房源"):
            f1, f2, f3 = st.columns(3)
            # 增加空值过滤并确保类型正确
            reg_options = sorted([str(x) for x in df['region'].unique() if x])
            room_options = sorted([str(x) for x in df['rooms'].unique() if x])
            
            sel_reg = f1.multiselect("区域", options=reg_options)
            sel_room = f2.multiselect("户型", options=room_options)
            
            # 价格滑块容错处理
            df['price_numeric'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            max_p_val = int(df['price_numeric'].max()) if not df.empty else 15000
            max_p = f3.slider("预算上限 (£/月)", 1000, max(15000, max_p_val), 15000)

        # 应用筛选
        f_df = df.copy()
        if sel_reg: f_df = f_df[f_df['region'].isin(sel_reg)]
        if sel_room: f_df = f_df[f_df['rooms'].isin(sel_room)]
        f_df = f_df[f_df['price_numeric'] <= max_p]
        
        # 排序：精选在前，日期在后
        f_df = f_df.sort_values(by=['is_featured', 'date'], ascending=[False, False])

        # 网格渲染
        cols = st.columns(3)
        for i, (idx, row) in enumerate(f_df.iterrows()):
            with cols[i % 3]:
                st.markdown('<div style="position: relative;">', unsafe_allow_html=True)
                # 置顶标签逻辑
                if str(row.get('is_featured')) == '1':
                    st.markdown('<div class="featured-badge">PREMIUM 精选</div>', unsafe_allow_html=True)
                
                with st.container(border=True):
                    # 关键：从 F 列读取图片并展示
                    poster_url = row.get('poster-link', '')
                    if isinstance(poster_url, str) and (poster_url.startswith("http") or poster_url.startswith("data:image")):
                        st.image(poster_url, use_container_width=True)
                    else:
                        st.info("📷 预览图加载中...")
                        
                    st.markdown(f"""
                        <div class="property-info-container">
                            <div class="prop-title">{row['title']}</div>
                            <div class="prop-price">£{int(row['price_numeric'])} /mo</div>
                            <div class="prop-tags">📍 {row['region']} | {row['rooms']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 这里的 idx+2 是为了对应 Google Sheets 的行号（跳过表头且索引从1开始）
                    if st.button("查看详情", key=f"view_{idx}", use_container_width=True):
                        show_details(row, worksheet, idx + 2)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("正在从数据库同步房源信息...")

# --- TAB 2, 3, 4 (原始全功能保留) ---
with tabs[1]:
    st.markdown("## 🛠️ 全生命周期管家式关怀")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""<div class="service-card"><div class="service-title">🏠 精准定向选址</div><p><b>Bespoke Property Search</b></p><ul><li><b>深度覆盖</b>：伦敦、曼彻斯特、伯明翰等核心区域。</li><li><b>多维筛选</b>：基于校区安全、通勤时间及周边族裔分布建模。</li></ul></div>""", unsafe_allow_html=True)
        st.markdown("""<div class="service-card"><div class="service-title">📜 文书合规与风控</div><p><b>Contract & Compliance</b></p><ul><li><b>租房审查协助</b>：针对留学生无英国担保人痛点提供专业方案。</li><li><b>合同审计</b>：深度解读 TA 合同，确保押金受 TDS 官方保护。</li></ul></div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown("""<div class="service-card"><div class="service-title">账单管家服务</div><p><b>Utility Setting-up</b></p><ul><li><b>全项托管</b>：协助开通水、电、煤气及高性价比宽带。</li><li><b>政务处理</b>：指导申请 Council Tax 免税。</li></ul></div>""", unsafe_allow_html=True)
        st.markdown("""<div class="service-card"><div class="service-title">🧹 轻松退房保障</div><p><b>Easy Check Out</b></p><ul><li><b>预检服务</b>：对照验房报告预检，确保押金全额退还。</li><li><b>深度清洁</b>：长期合作的靠谱清洁团队。</li></ul></div>""", unsafe_allow_html=True)

with tabs[2]:
    st.markdown("## 👤 团队背景")
    st.markdown("""
    <div class="bio-box">
        <h3 style="color:#bfa064;">十年磨一剑，专注英伦高端租赁</h3>
        <p style="font-size:16px; line-height:1.8;">
            <span class="highlight-gold">● 名校精英视角：</span> 创始人拥有 <b>UCL 本硕学位</b>。<br>
            <span class="highlight-gold">● 行业巨头背景：</span> 曾任职于全球房产咨询五大行 <b>JLL（仲量联行）</b>。<br>
            <span class="highlight-gold">● 十载英伦深耕：</span> 扎根英国生活 <b>10余年</b>，提供治安解析及未来价值研判。<br>
            <span class="highlight-gold">● 官方战略合作：</span> 与英国顶尖开发商建立深厚合作，掌握内部房源。
        </p>
    </div>
    """, unsafe_allow_html=True)

with tabs[3]:
    st.markdown("## 📞 立即咨询")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""<div style="background:#f8f9fa; padding:40px; border-radius:20px; text-align:center; border:1px solid #eee;"><p style="color:#888;">扫描或添加微信 ID</p><h2 style="color:#1a1a1a; margin:10px 0;">HaoHarbour</h2><hr><p style="color:#888;">紧急咨询 (WhatsApp)</p><a href="https://wa.me/447450912493" class="wa-link">💬 点击发起对话</a></div>""", unsafe_allow_html=True)
