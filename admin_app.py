import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary.uploader
import pandas as pd
import io, requests
from datetime import datetime

# --- 1. 基础配置与云端 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")
cloudinary.config(cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"], api_key=st.secrets["CLOUDINARY_API_KEY"], api_secret=st.secrets["CLOUDINARY_API_SECRET"])

# --- 2. 核心函数 ---
def create_poster(files, title_text):
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try: font_t = ImageFont.truetype("simhei.ttf", 45); font_f = ImageFont.truetype("simhei.ttf", 25)
        except: font_t = font_f = ImageFont.load_default()
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))
        draw.text((40, 950), title_text, font=font_t, fill=(0, 0, 0))
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_f, fill=(180, 160, 100))
        return canvas
    except: return None

# --- 3. 界面逻辑 ---
tab1, tab2 = st.tabs(["🆕 发布新房源", "📊 数据看板与管理"])

with tab1:
    st.subheader("录入房源")
    c1, c2 = st.columns(2)
    with c1:
        t_title = st.text_input("标题")
        t_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"])
        t_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"])
        t_price = st.number_input("月租 (£)", value=3000)
    with c2:
        t_desc = st.text_area("展示描述", height=150)
        t_pics = st.file_uploader("海报照片", accept_multiple_files=True)
        if st.button("🚀 立即发布", type="primary"):
            p = create_poster(t_pics, t_title)
            if p:
                buf = io.BytesIO(); p.save(buf, format='JPEG')
                url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": t_title, "region": t_reg, "rooms": t_room, "price": t_price, "poster-link": url, "description": t_desc, "views": 0, "is_featured": False}
                conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("发布成功！"); st.rerun()

with tab2:
    st.subheader("📈 全量房源管理")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not df.empty:
            # 解决 NaN 转换问题
            df['price'] = df['price'].fillna(0).astype(int)
            df['views'] = df['views'].fillna(0).astype(int)
            df['is_featured'] = df['is_featured'].fillna(False)

            # 1. 核心表格展示 (显示日期、标题、价格、房型、点击量)
            st.write("---")
            # 增加一个显示用的列，方便区分重名
            display_df = df.copy()
            display_df.insert(0, "操作ID", df.index) 
            st.dataframe(display_df[['操作ID', 'date', 'title', 'price', 'rooms', 'views', 'is_featured']], use_container_width=True)

            # 2. 交互式修改区
            st.write("---")
            sel_id = st.number_input("👉 输入上方表格中的【操作ID】进行精准编辑", min_value=0, max_value=len(df)-1, step=1)
            
            # 精准抓取该行数据（解决重名问题）
            row = df.iloc[sel_id]
            st.info(f"正在管理: **{row['title']}** (发布日期: {row['date']})")

            # 快捷功能按钮
            b1, b2, b3 = st.columns(3)
            if b1.button("🔄 Refresh (置顶该房源)", use_container_width=True):
                df.at[sel_id, 'date'] = datetime.now().strftime("%Y-%m-%d")
                conn.update(worksheet="Sheet1", data=df); st.rerun()
            
            f_label = "⭐ 取消精选" if row['is_featured'] else "🌟 设为精选"
            if b2.button(f_label, use_container_width=True):
                df.at[sel_id, 'is_featured'] = not row['is_featured']
                conn.update(worksheet="Sheet1", data=df); st.rerun()

            if b3.button("🗑️ 确认下架 (从表格删除)", type="secondary", use_container_width=True):
                df = df.drop(df.index[sel_id])
                conn.update(worksheet="Sheet1", data=df); st.rerun()

            # 编辑表单
            with st.form("edit_precise"):
                st.write("📝 修改详细信息 (Edit Details)")
                e_title = st.text_input("标题", value=row['title'])
                e_price = st.number_input("月租价格", value=int(row['price']))
                e_desc = st.text_area("描述亮点", value=row.get('description', ''), height=200)
                if st.form_submit_button("💾 保存全部修改", type="primary"):
                    df.at[sel_id, 'title'] = e_title
                    df.at[sel_id, 'price'] = e_price
                    df.at[sel_id, 'description'] = e_desc
                    conn.update(worksheet="Sheet1", data=df)
                    st.success("更新成功！"); st.rerun()
        else:
            st.info("暂无数据。")
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
