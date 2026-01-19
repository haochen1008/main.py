import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import pandas as pd
import io
import requests
from datetime import datetime

# --- 1. 页面与配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="wide")

cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)
DEEPSEEK_KEY = st.secrets["OPENAI_API_KEY"] 

# --- 2. 核心函数：海报合成与 AI 提取 ---
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

        for i, f in enumerate(files[:6]):
            img = Image.open(f).convert('RGB').resize((390, 300), Image.Resampling.LANCZOS)
            canvas.paste(img, (5 + (i % 2) * 395, 5 + (i // 2) * 305))

        wm_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(wm_layer).text((180, 450), "Hao Harbour", font=font_wm, fill=(255, 255, 255, 120))
        rotated_wm = wm_layer.rotate(30, expand=False)
        canvas.paste(rotated_wm, (0, 0), rotated_wm)

        draw.text((40, 950), title_text, font=font_title, fill=(0, 0, 0))
        draw.line([(40, 1010), (760, 1010)], fill=(200, 200, 200), width=2)
        draw.text((40, 1030), "Hao Harbour | London Excellence", font=font_footer, fill=(180, 160, 100))
        return canvas
    except Exception as e:
        st.error(f"海报合成失败: {e}"); return None

def call_ai(text):
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        prompt = f"翻译并精简成中文要点，需包含Available date，✔开头，禁止押金：\n{text}"
        res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                            headers=headers, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]})
        return res.json()['choices'][0]['message']['content']
    except: return "AI 提取失败"

# --- 3. 主界面 ---
tab1, tab2 = st.tabs(["🆕 发布新房源", "⚙️ 管理已有房源"])

# --- 发布标签页 ---
with tab1:
    c1, c2 = st.columns(2)
    if "ai_draft" not in st.session_state: st.session_state.ai_draft = ""
    with c1:
        st.subheader("1. 输入基本信息")
        t_title = st.text_input("标题", key="new_t")
        t_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"], key="new_r")
        t_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"], key="new_rm")
        t_price = st.number_input("月租 (£)", value=3000, key="new_p")
        t_raw = st.text_area("英文描述内容", height=150)
        if st.button("✨ AI 智能提取"):
            st.session_state.ai_draft = call_ai(t_raw)
    with c2:
        st.subheader("2. 预览与合成")
        t_desc = st.text_area("最终展示描述", value=st.session_state.ai_draft, height=200)
        t_pics = st.file_uploader("上传照片 (合成海报)", accept_multiple_files=True)
        if st.button("🚀 确认发布", type="primary"):
            if not t_title or not t_pics: st.error("标题和照片不能为空")
            else:
                poster = create_poster(t_pics, t_title)
                if poster:
                    buf = io.BytesIO(); poster.save(buf, format='JPEG')
                    url = cloudinary.uploader.upload(buf.getvalue())['secure_url']
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                    new_row = {"date": datetime.now().strftime("%Y-%m-%d"), "title": t_title, "region": t_reg, 
                               "rooms": t_room, "price": t_price, "poster-link": url, "description": t_desc, 
                               "views": 0, "is_featured": False}
                    conn.update(worksheet="Sheet1", data=pd.concat([df, pd.DataFrame([new_row])]))
                    st.success("发布成功！")

# --- 管理标签页 (全新交互设计) ---
with tab2:
    st.subheader("📊 房源快捷管理")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if not df.empty:
            # 第一步：点击选择房子
            selected_title = st.selectbox("🎯 第一步：选择一个你想修改的房子", df['title'].tolist())
            current_item = df[df['title'] == selected_title].iloc[0]
            
            st.divider()
            
            # 第二步：显示该房子的快速操作按钮
            st.write(f"### ⚡ 快捷操作: {selected_title}")
            b1, b2, b3, b4 = st.columns(4)
            
            with b1:
                if st.button("🔄 Refresh (置顶)", use_container_width=True):
                    df.loc[df['title'] == selected_title, 'date'] = datetime.now().strftime("%Y-%m-%d")
                    conn.update(worksheet="Sheet1", data=df)
                    st.toast("已刷新日期并置顶！"); st.rerun()
            
            with b2:
                is_f = current_item.get('is_featured', False)
                f_label = "⭐ 取消精选" if is_f else "🌟 设为精选"
                if st.button(f_label, use_container_width=True):
                    df.loc[df['title'] == selected_title, 'is_featured'] = not is_f
                    conn.update(worksheet="Sheet1", data=df); st.rerun()
            
            with b3:
                if st.button("🗑️ 下架房子", type="secondary", use_container_width=True):
                    conn.update(worksheet="Sheet1", data=df[df['title'] != selected_title]); st.rerun()

            with b4:
                # 统计显示
                st.write(f"👁️ 浏览量: {int(current_item.get('views', 0))}")

            # 第三步：Edit 详细信息更改
            st.write("---")
            st.write("### 📝 Edit (更改房源信息)")
            with st.form("edit_form"):
                e_title = st.text_input("标题", value=current_item['title'])
                e_price = st.number_input("价格 (£/pcm)", value=int(current_item['price']))
                e_reg = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"], 
                                   index=["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"].index(current_item['region']) if current_item['region'] in ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦", "其它"] else 0)
                e_room = st.selectbox("房型", ["Studio", "1房", "2房", "3房", "4房+"], 
                                    index=["Studio", "1房", "2房", "3房", "4房+"].index(current_item['rooms']) if current_item['rooms'] in ["Studio", "1房", "2房", "3房", "4房+"] else 0)
                e_desc = st.text_area("描述亮点内容", value=current_item.get('description', ''), height=150)
                
                if st.form_submit_button("💾 保存更改", type="primary", use_container_width=True):
                    idx = df.index[df['title'] == selected_title].tolist()[0]
                    df.at[idx, 'title'] = e_title
                    df.at[idx, 'price'] = e_price
                    df.at[idx, 'region'] = e_reg
                    df.at[idx, 'rooms'] = e_room
                    df.at[idx, 'description'] = e_desc
                    conn.update(worksheet="Sheet1", data=df)
                    st.success("信息已更新！"); st.rerun()

            st.write("---")
            st.write("🔍 全表预览")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无房源，请先录入。")
    except Exception as e:
        st.error(f"连接数据库出错: {e}")
