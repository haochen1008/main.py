import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests
from datetime import datetime

# --- 1. 配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
cloudinary.config(cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"], api_key=st.secrets["CLOUDINARY_API_KEY"], api_secret=st.secrets["CLOUDINARY_API_SECRET"])
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"]

# --- 2. 工具函数 ---
def call_ai_logic(text):
    """通用的 AI 提取逻辑"""
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，使用✔开头，禁止提及押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]})
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI 提取失败: {str(e)}"

def create_poster(files, title_text):
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        # 尝试加载字体，失败则使用默认
        try: font_t = ImageFont.truetype("simhei.ttf", 45); font_f = ImageFont.truetype("simhei.ttf", 25)
        except: font_t = font_f = ImageFont.load_default()
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        draw.text((40, 950), title_text, font=font_t, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_f, fill=(180, 160, 100))
        return canvas
    except: return None

# --- 3. 页面布局 ---
tab1, tab2 = st.tabs(["🆕 发布房源", "⚙️ 管理中心"])

# --- 发布逻辑 ---

with tab1:
    st.subheader("🚀 发布新房源")
    if "new_ai_desc" not in st.session_state: st.session_state.new_ai_desc = ""
    
    col_a, col_b = st.columns(2)
    with col_a:
        n_title = st.text_input("房源名称 (例如: River Park Tower)")
        n_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        n_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        n_price = st.number_input("月租 (£/pcm)", value=3000)
        n_raw = st.text_area("粘贴英文原始描述", height=150)
        poster_link = st.text_input("房源海报链接 (Poster URL)")
        if st.button("✨ 执行 AI 提取", key="btn_new_ai"):
            st.session_state.new_ai_desc = call_ai_logic(n_raw)
            
    with col_b:
        n_desc = st.text_area("编辑 AI 提取结果", value=st.session_state.new_ai_desc, height=200)
        n_pics = st.file_uploader("上传图片（最少6张效果最佳）", accept_multiple_files=True)
        if st.button("📤 确认发布并生成海报", type="primary"):
            poster = create_poster(n_pics, n_title)
            if poster:
                buf = io.BytesIO(); poster.save(buf, format='JPEG')
                url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": n_title, "region": n_reg, "rooms": n_room, "price": n_price, "poster-link": url, "description": n_desc, "views": 0, "is_featured": False}
                conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("房源已发布！"); st.rerun()

# --- 管理逻辑 ---


with tab2:
    st.subheader("📊 房源看板与快捷编辑")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not df.empty:
            # 数据清洗，防止 NaN 导致报错
            df['price'] = df['price'].fillna(0).astype(int)
            df['views'] = df['views'].fillna(0).astype(int)
            
            # 1. 核心看板表格
            st.write("---")
            display_df = df.copy()
            display_df.insert(0, "ID", df.index)
            st.dataframe(display_df[['ID', 'date', 'title', 'region', 'price', 'rooms', 'views', 'is_featured']], use_container_width=True)

            total_views = df['views'].sum()
            st.metric("📈 网页总点击量", int(total_views))

            # 2. 选房编辑区
            st.write("---")
            col_sel, col_stat = st.columns([1, 1])
            with col_sel:
                # 使用带 ID 的标题防止重名房子混淆
                options = [f"{i} | {row['title']} (£{row['price']})" for i, row in df.iterrows()]
                selected_option = st.selectbox("🎯 选择要编辑的房源", options)
                sel_id = int(selected_option.split(" | ")[0])
                row = df.iloc[sel_id]
            
            # 3. 快速操作按钮
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔄 Refresh (置顶房源)", use_container_width=True):
                    df.at[sel_id, 'date'] = datetime.now().strftime("%Y-%m-%d")
                    conn.update(worksheet="Sheet1", data=df); st.rerun()
            with c2:
                is_f = row.get('is_featured', False)
                if st.button("🌟 取消精选" if is_f else "🌟 设为精选", use_container_width=True):
                    df.at[sel_id, 'is_featured'] = not is_f
                    conn.update(worksheet="Sheet1", data=df); st.rerun()
            with c3:
                if st.button("🗑️ 立即下架房源", type="secondary", use_container_width=True):
                    df = df.drop(df.index[sel_id])
                    conn.update(worksheet="Sheet1", data=df); st.rerun()

            # 4. 详细修改表单 (找回 AI 功能)
            with st.expander("📝 修改房源详细内容 (含 AI 提取)", expanded=True):
                with st.form("edit_form_final"):
                    e_title = st.text_input("修改标题", value=row['title'])
                    e_price = st.number_input("修改月租", value=int(row['price']))
                    e_desc = st.text_area("描述亮点 (支持手动修改或 AI 覆盖)", value=row.get('description', ''), height=200)
                    
                    st.caption("提示：如需重新提取描述，请在发布页提取后复制到此处，或在此处直接修改。")
                    if st.form_submit_button("💾 保存所有修改", type="primary", use_container_width=True):
                        df.at[sel_id, 'title'] = e_title
                        df.at[sel_id, 'price'] = e_price
                        df.at[sel_id, 'description'] = e_desc
                        conn.update(worksheet="Sheet1", data=df)
                        st.success("修改成功！"); st.rerun()
        else:
            st.info("暂无房源数据。")
    except Exception as e:
        st.error(f"连接出错: {str(e)}")
