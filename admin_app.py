import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

# 配置云端服务
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] 

# --- 核心：海报合成发动机 (找回丢失的合成逻辑) ---
def create_poster(files, title_text):
    try:
        canvas = Image.new('RGB', (800, 1200), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        try:
            font_title = ImageFont.truetype("simhei.ttf", 45)
            font_footer = ImageFont.truetype("simhei.ttf", 25)
            font_wm = ImageFont.truetype("simhei.ttf", 80)
        except:
            font_title = font_footer = font_wm = ImageFont.load_default()

        # 6 宫格拼接
        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))

        # 水印
        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(wm_layer).text((180, 450), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        # 底部信息
        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        return canvas
    except Exception as e:
        st.error(f"海报合成失败: {e}"); return None

# --- AI 提取函数 ---
def call_ai_summary(text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，✔开头，禁止押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]})
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取失败，请手动输入"

# --- 界面逻辑 ---
if "ai_desc" not in st.session_state: st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布房源", "📊 数据管理"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("房源名称")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000)
        raw_desc = st.text_area("粘贴英文描述")
        if st.button("✨ 执行 AI 提取"): 
            st.session_state.ai_desc = call_ai_summary(raw_desc)
    with c2:
        final_desc = st.text_area("最终描述", value=st.session_state.ai_desc, height=200)
        pics = st.file_uploader("上传照片", accept_multiple_files=True)
        if st.button("🚀 确认发布", type="primary"):
            poster = create_poster(pics, title)
            if poster:
                buf = io.BytesIO(); poster.save(buf, format='JPEG')
                url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                conn = st.connection("gsheets", type=GSheetsConnection)
                df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": title, "region": region, 
                           "rooms": rooms, "price": price, "poster-link": url, "description": final_desc, 
                           "views": 0, "is_featured": False}
                conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])]))
                st.success("发布成功！")

with tab2:
    st.subheader("📊 房源数据管理")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 获取最新数据
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not df.empty:
            # 顶部统计
            st.metric("总曝光量 (Total Views)", int(df['views'].sum()) if 'views' in df.columns else 0)
            
            # 选择要操作的房源
            target_title = st.selectbox("选择要处理的房源", df['title'].tolist())
            item_data = df[df['title'] == target_title].iloc[0]
            
            # 操作按钮行
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            # --- 核心：修改功能 (Edit) ---
            with st.expander(f"📝 修改房源信息: {target_title}"):
                with st.form(key="edit_form"):
                    new_title = st.text_input("修改标题", value=item_data['title'])
                    new_price = st.number_input("修改价格 (£/pcm)", value=int(item_data['price']))
                    new_region = st.selectbox("修改区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "成外"], 
                                            index=["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "成外"].index(item_data['region']) if item_data['region'] in ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "成外"] else 0)
                    new_rooms = st.selectbox("修改房型", ["1房", "2房", "3房", "4房+"], 
                                           index=["1房", "2房", "3房", "4房+"].index(item_data['rooms']) if item_data['rooms'] in ["1房", "2房", "3房", "4房+"] else 0)
                    new_desc = st.text_area("修改描述 (支持复制)", value=item_data.get('description', ""), height=150)
                    
                    submit_edit = st.form_submit_button("💾 保存修改", type="primary")
                    
                    if submit_edit:
                        # 更新当前行数据
                        idx = df.index[df['title'] == target_title].tolist()[0]
                        df.at[idx, 'title'] = new_title
                        df.at[idx, 'price'] = new_price
                        df.at[idx, 'region'] = new_region
                        df.at[idx, 'rooms'] = new_rooms
                        df.at[idx, 'description'] = new_desc
                        
                        conn.update(worksheet="Sheet1", data=df)
                        st.success(f"✅ {target_title} 的信息已更新！")
                        st.rerun()

            # --- 其他快捷功能 ---
            with col_btn1:
                if st.button("🔄 刷新日期 (置顶)", use_container_width=True):
                    df.loc[df['title'] == target_title, 'date'] = datetime.now().strftime("%Y-%m-%d")
                    conn.update(worksheet="Sheet1", data=df)
                    st.toast("日期已更新，房源已置顶")
                    st.rerun()
            
            with col_btn2:
                is_f = item_data.get('is_featured', False)
                btn_label = "⭐ 取消精选" if is_f else "🌟 设为精选"
                if st.button(btn_label, use_container_width=True):
                    df.loc[df['title'] == target_title, 'is_featured'] = not is_f
                    conn.update(worksheet="Sheet1", data=df)
                    st.rerun()
                    
            with col_btn3:
                if st.button("🗑️ 下架房源", type="secondary", use_container_width=True):
                    new_df = df[df['title'] != target_title]
                    conn.update(worksheet="Sheet1", data=new_df)
                    st.warning("房源已删除")
                    st.rerun()

            st.divider()
            st.write("### 当前房源列表预览")
            st.dataframe(df, use_container_width=True)
            
        else:
            st.info("目前还没有房源数据，请先在‘发布’页面录入。")
            
    except Exception as e:
        st.error(f"数据连接失败，请检查网络或 GSheets 配置。错误: {e}")
