import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import json
import base64

# --- 1. 配置 ---
# 从 Secrets 获取 API Key
try:
    IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]
except:
    st.error("请在 Streamlit Secrets 中配置 IMGBB_API_KEY")
    st.stop()

# --- 2. 核心函数：加水印并上传 ---
def process_and_upload(image_input):
    try:
        # 加载图片
        img = Image.open(image_input).convert("RGBA")
        
        # 创建水印层
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # 字体大小自适应
        f_size = int(img.size[0] / 12)
        font = ImageFont.load_default() # 云端建议使用默认字体防止路径报错
        
        text = "Hao Harbour"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # 绘制半透明白色水印 (居中)
        draw.text(((img.size[0]-w)/2, (img.size[1]-h)/2), text, fill=(255, 255, 255, 120), font=font)
        
        # 合并
        final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
        buf = BytesIO()
        final_img.save(buf, format="JPEG", quality=85)
        
        # 上传到 ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(buf.getvalue())
        }
        res = requests.post(url, data=payload)
        return res.json()['data']['url']
    except Exception as e:
        st.error(f"处理失败: {e}")
        return None

# --- 3. 界面逻辑 ---
st.title("🏡 Hao Harbour 后台管理")

conn = st.connection("gsheets", type=GSheetsConnection)

with st.form("listing_form"):
    title = st.text_input("房源标题")
    region = st.selectbox("区域", ["London Bridge", "Bermondsey", "Canary Wharf", "Other"])
    price = st.number_input("月租 (£/pcm)", value=3000)
    rooms = st.text_input("房型")
    
    # 改为上传文件，这样水印效果最好
    uploaded_file = st.file_uploader("上传房源封面图", type=["jpg", "jpeg", "png"])
    raw_desc = st.text_area("粘贴原始描述 (AI 提取)")
    
    if st.form_submit_button("✨ 智能提取并发布"):
        if not uploaded_file or not title:
            st.warning("请填写标题并上传图片")
        else:
            with st.spinner("正在加水印并同步至云端..."):
                # 1. 自动处理水印并上传
                final_url = process_and_upload(uploaded_file)
                
                if final_url:
                    # 2. 写入 Sheets (这里简化了 AI 提取，直接存入)
                    new_data = pd.DataFrame([{
                        "title": title,
                        "region": region,
                        "rooms": rooms,
                        "price": price,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "description": raw_desc, # 如果你有 AI 函数，可以在这里调用
                        "poster-link": final_url
                    }])
                    
                    df = conn.read(worksheet="Sheet1")
                    updated_df = pd.concat([new_data, df], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    st.success("发布成功！")
                    st.image(final_url, caption="带水印预览")
# --- 4. 主界面布局 ---
st.title("🏡 Hao Harbour 房源发布与管理")

# 初始化 Session State 用于预览
if "ai_desc" not in st.session_state: st.session_state.ai_desc = ""

tab1, tab2 = st.tabs(["🆕 发布新房源", "🗂️ 房源管理 (删除)"])

# --- TAB 1: 发布房源 ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. 填写基本信息")
        title = st.text_input("房源名称 (如: Merino Gardens)")
        region = st.selectbox("区域", ["中伦敦", "东伦敦", "西伦敦", "南伦敦", "北伦敦"])
        rooms = st.selectbox("房型", ["1房", "2房", "3房", "4房+"])
        price = st.number_input("月租 (£/pcm)", value=3000, step=100)
        
        raw_desc = st.text_area("粘贴英文原始描述 (用于 AI 提取)", height=200)
        if st.button("✨ 执行 AI 智能提取"):
            if raw_desc:
                with st.spinner("DeepSeek 正在分析中..."):
                    st.session_state.ai_desc = call_ai_summary(raw_desc)
            else:
                st.warning("请先粘贴英文描述")

    with col2:
        st.subheader("2. 预览与发布")
        # AI 提取后的结果，允许手动微调
        final_desc = st.text_area("最终 Description (可微调)", value=st.session_state.ai_desc, height=250)
        
        photos = st.file_uploader("上传照片 (前6张将生成海报)", accept_multiple_files=True)
        
        if st.button("🚀 确认发布 (生成海报并同步)", type="primary"):
            if not title or not photos or not final_desc:
                st.error("请确保标题、描述和图片已准备就绪")
            else:
                with st.spinner("正在生成海报并上传云端..."):
                    # 生成海报
                    poster_img = create_poster(photos, title)
                    if poster_img:
                        # 转为字节流上传
                        buf = io.BytesIO()
                        poster_img.save(buf, format='JPEG')
                        upload_res = cloudinary.uploader.upload(buf.getvalue())
                        p_url = upload_res.get("secure_url")
                        
                        # 同步 Google Sheets (追加模式)
                        try:
                            conn = st.connection("gsheets", type=GSheetsConnection)
                            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
                            
                            new_data = {
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "title": title,
                                "region": region,
                                "rooms": rooms,
                                "price": price,
                                "poster-link": p_url,
                                "description": final_desc
                            }
                            updated_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                            conn.update(worksheet="Sheet1", data=updated_df)
                            
                            st.success(f"✅ 《{title}》 已成功追加至数据库！")
                            st.image(p_url, caption="生成的海报已同步至客户端", width=400)
                        except Exception as e:
                            st.error(f"数据库同步失败: {e}")

# --- TAB 2: 房源管理 (删除) ---
with tab2:
    st.subheader("📋 现有房源在线列表")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        manage_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how='all')
        
        if manage_df.empty:
            st.info("暂无在线房源")
        else:
            # 删除功能
            to_delete = st.multiselect("选择要下架(删除)的房源标题", options=manage_df['title'].tolist())
            
            if st.button("🗑️ 确认下架选中房源"):
                if to_delete:
                    # 过滤掉要删除的行
                    new_df = manage_df[~manage_df['title'].isin(to_delete)]
                    conn.update(worksheet="Sheet1", data=new_df)
                    st.success(f"已下架: {len(to_delete)} 套房源")
                    st.rerun()
                else:
                    st.warning("请先选择房源")
            
            # 展示数据
            st.dataframe(manage_df[['date', 'title', 'region', 'rooms', 'price']], use_container_width=True)
            
    except Exception as e:
        st.error(f"列表加载失败: {e}")
