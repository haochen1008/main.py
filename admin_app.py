import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import base64

# --- 1. 配置（请务必填入你的 ImgBB API KEY） ---
IMGBB_API_KEY = "deedcd3d644b02b49452f364785e9fdd"

# --- 2. 核心：自动加水印并上传图床函数 ---
def process_and_upload_image(image_input):
    """
    输入：可以是图片链接(str) 或 上传的文件对象(bytes)
    输出：带水印图片的 ImgBB 直链
    """
    try:
        # 加载图片
        if isinstance(image_input, str):
            resp = requests.get(image_input)
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
        else:
            img = Image.open(image_input).convert("RGBA")
        
        # --- 画水印 ---
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        # 字体大小自适应（宽度的1/12）
        f_size = int(img.size[0] / 12)
        try:
            font = ImageFont.load_default() 
        except:
            font = ImageFont.load_default()
        
        text = "Hao Harbour"
        # 计算居中位置
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((img.size[0]-w)/2, (img.size[1]-h)/2), text, fill=(255, 255, 255, 100), font=font)
        
        # 合并并压缩
        final_img = Image.alpha_composite(img, txt_layer).convert("RGB")
        buf = BytesIO()
        final_img.save(buf, format="JPEG", quality=85)
        img_bytes = buf.getvalue()

        # --- 上传到 ImgBB ---
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(img_bytes)
        }
        res = requests.post(url, data=payload)
        return res.json()['data']['url']
    except Exception as e:
        st.error(f"图片水印处理或上传失败: {e}")
        return None

# --- 3. 你的保存/发布按钮逻辑 ---
# 假设你原来的按钮逻辑如下，我们只需要植入 process_and_upload_image 这一步
if st.button("🚀 执行发布"):
    if poster_link: # 假设 poster_link 是你在界面上输入的原始图片地址
        with st.spinner("正在生成带水印海报并发布..."):
            
            # 【关键一步】将原始链接转化为带水印的新链接
            final_watermarked_url = process_and_upload_image(poster_link)
            
            if final_watermarked_url:
                # 使用这个新的 final_watermarked_url 写入 Google Sheets
                new_row = pd.DataFrame([{
                    "title": title,
                    "region": region,
                    "rooms": rooms,
                    "price": price,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "description": processed_desc, # 你原来的 AI 描述
                    "poster-link": final_watermarked_url # 存储带水印的链接
                }])
                
                # ... 执行你原有的 conn.update() 逻辑 ...
                st.success("发布成功！客户端现在看到的就是带水印的图了。")
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
