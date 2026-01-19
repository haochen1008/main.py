import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import json # 用于解析 ImgBB 的响应

# --- ImgBB API 配置 (请替换为你的真实 Key) ---
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"] # 推荐使用 Streamlit Secrets 管理

# --- 1. Streamlit 页面配置 ---
st.set_page_config(page_title="Hao Harbour Admin", layout="centered")
st.title("🏡 Hao Harbour 房源管理")
st.subheader("🤖 AI 智能提取 & 自动发布")

# --- 2. GSheets 连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 核心功能：图片加水印函数 ---
def apply_watermark(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        
        txt = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt)
        
        font_size = int(img.size[0] / 12)
        try:
            # 优先使用一个常见的无衬线字体，提高兼容性
            font = ImageFont.truetype("arial.ttf", font_size) 
        except IOError:
            font = ImageFont.load_default() # 如果 'arial.ttf' 不存在，使用默认字体
        
        text = "Hao Harbour"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img.size[0] - w) / 2
        y = (img.size[1] - h) / 2
        
        draw.text((x, y), text, fill=(255, 255, 255, 100), font=font)
        
        combined = Image.alpha_composite(img, txt).convert("RGB")
        
        # 将带水印图片保存到 BytesIO 对象，以便上传
        img_byte_arr = BytesIO()
        combined.save(img_byte_arr, format='JPEG', quality=85) # 保存为 JPEG，减少文件大小
        img_byte_arr.seek(0) # 将指针移到文件开头
        return img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"图片加水印失败: {e}")
        return None

# --- 4. 核心功能：上传图片到 ImgBB ---
def upload_to_imgbb(image_bytes):
    if not IMGBB_API_KEY:
        st.error("ImgBB API Key 未配置。请在 Streamlit Secrets 中设置 'IMGBB_API_KEY'。")
        return None
        
    url = "https://api.imgbb.com/1/upload"
    files = {'image': image_bytes}
    data = {'key': IMGBB_API_KEY}
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status() # 如果请求失败，抛出异常
        result = json.loads(response.text)
        
        if result['status'] == 200:
            return result['data']['url']
        else:
            st.error(f"ImgBB 上传失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求错误或 ImgBB API 访问失败: {e}")
        return None
    except json.JSONDecodeError:
        st.error("ImgBB 返回了无效的 JSON 响应。")
        return None

# --- 5. AI 提取描述函数 (这部分保持你原来的代码) ---
# 假设你有一个名为 call_ai_summary 的函数
# 示例：
def call_ai_summary(raw_text):
    # 这里应该替换为你的真实 AI API 调用
    # 例如：通过 OpenAI, Coze, Gemini 等获取总结
    if "卧室" in raw_text and "浴室" in raw_text:
        return f"这是一套精美的房源，AI总结：{raw_text[:100]}..."
    else:
        return f"AI总结：{raw_text[:100]}..."
    # return "AI_PROCESSED_DESCRIPTION_HERE" 

# --- 6. 房源录入表单 ---
st.header("📝 录入新房源")

with st.form("new_listing_form"):
    title = st.text_input("房源标题", "Modern 2-bed flat near London Bridge")
    region = st.text_input("区域", "Bermondsey")
    rooms = st.text_input("房型", "2 Beds, 2 Baths")
    price = st.number_input("月租金 (£)", min_value=1000, value=3000, step=100)
    
    # 【核心改动】: 文件上传器
    uploaded_file = st.file_uploader("上传房源封面图片 (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    raw_description = st.text_area("房源原始描述 (AI将从这里提取亮点)", 
                                   "A stunning two-bedroom, two-bathroom apartment located in the heart of London, "
                                   "just a 5-minute walk from London Bridge station. Features include a spacious "
                                   "living area, fully fitted kitchen, and panoramic city views. Available for rent now.")
    
    submitted = st.form_submit_button("🚀 执行智能提取并发布")

    if submitted:
        if not uploaded_file:
            st.error("请上传房源封面图片。")
            st.stop()
            
        with st.spinner("正在处理图片、上传并提取描述..."):
            # 1. 读取上传的图片文件
            original_image_bytes = uploaded_file.getvalue()
            
            # 2. 加水印
            watermarked_image_bytes = apply_watermark(original_image_bytes)
            
            if watermarked_image_bytes:
                # 3. 上传到 ImgBB
                poster_link = upload_to_imgbb(watermarked_image_bytes)
                
                if poster_link:
                    st.success(f"图片已成功上传至: {poster_link}")
                    st.image(watermarked_image_bytes, caption="带水印的封面预览", use_container_width=True)
                    
                    # 4. AI 提取描述
                    processed_desc = call_ai_summary(raw_description)
                    st.success("AI 描述已提取。")
                    
                    # 5. 准备数据并写入 Google Sheets
                    new_data = pd.DataFrame([{
                        "title": title,
                        "region": region,
                        "rooms": rooms,
                        "price": price,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "description": processed_desc,
                        "poster-link": poster_link # 这里存储的是带水印的图片链接
                    }])
                    
                    try:
                        # 尝试读取现有数据
                        existing_df = conn.read(worksheet="Sheet1", usecols=list(new_data.columns), ttl=0)
                        # 合并新数据
                        updated_df = pd.concat([new_data, existing_df], ignore_index=True)
                        # 写入 Google Sheets
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("🎉 房源已成功发布到 Google Sheets！")
                    except Exception as e:
                        st.error(f"写入 Google Sheets 失败: {e}")
                else:
                    st.error("图片上传 ImgBB 失败。")
            else:
                st.error("水印处理失败，无法继续。")
    else:
        st.info("请填写所有房源信息并上传图片。")

# --- 7. 管理现有房源 (示例，保持你原先的查看、编辑、删除逻辑) ---
st.header("📋 管理现有房源")
try:
    existing_data = conn.read(worksheet="Sheet1", ttl=0)
    st.dataframe(existing_data, use_container_width=True)
    
    # 示例: 如果你有编辑/删除按钮，它们也在这里。
    # 例如：
    # if st.button("刷新数据"):
    #     st.rerun()
    
except Exception as e:
    st.warning(f"无法加载现有房源数据: {e}")

st.divider()
st.caption("© 2026 Hao Harbour Properties.")
