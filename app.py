import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image

st.set_page_config(page_title="StoreHub AI Portal", layout="wide")

st.title("🚀 StoreHub CX: AI Escalation & Insights Tool")
st.markdown("---")

# 1. ส่วนตั้งค่า Keys
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key (anon public)", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# 2. ส่วนรับข้อมูล
st.header("📥 1. บันทึกเคสใหม่ (รองรับหลายไฟล์ภาพ/วิดีโอ)")
col1, col2 = st.columns(2)

with col1:
    store_name = st.text_input("ชื่อร้านค้า")
    customer_contact = st.text_input("อีเมล / เบอร์ติดต่อ")
    uploaded_files = st.file_uploader("📸 แนบหลักฐาน (เลือกได้หลายไฟล์ภาพหรือวิดีโอ)", 
                                    type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], 
                                    accept_multiple_files=True)

with col2:
    raw_complaint = st.text_area("ข้อความแจ้งปัญหาเบื้องต้น", height=150)

if st.button("✨ ส่งข้อมูลและให้ AI ประมวลผล", type="primary"):
    if not (supabase_url and supabase_key and gemini_key):
        st.error("❌ กรุณากรอกข้อมูล Keys ให้ครบถ้วน")
    else:
        with st.spinner("AI กำลังค้นหารุ่นที่รองรับและวิเคราะห์ข้อมูล..."):
            try:
                genai.configure(api_key=gemini_key)
                
                # --- ระบบค้นหาชื่อรุ่นอัตโนมัติเพื่อแก้ปัญหา 404 ---
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # เรียงลำดับความฉลาด: flash 1.5 -> flash -> pro
                target_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']
                
                selected_model_name = None
                for target in target_models:
                    if target in available_models:
                        selected_model_name = target
                        break
                
                if not selected_model_name:
                    selected_model_name = available_models[0] # ใช้ตัวแรกที่หาเจอถ้าไม่ตรงเงื่อนไข
                
                model = genai.GenerativeModel(selected_model_name)
                # ---------------------------------------------

                content = [f"วิเคราะห์ปัญหานี้ของลูกค้า StoreHub: {raw_complaint}"]
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if uploaded_file.type.startswith('image'):
                            img = Image.open(uploaded_file)
                            content.append(img)
                
                prompt = """ตอบเป็น JSON ภาษาไทยเท่านั้น:
                {
                  "category": "Hardware/Software/Payment/UserError",
                  "churn_risk": 1-5,
                  "elaborated_summary": "สรุปอาการเชิงเทคนิคและวิธีแก้"
                }"""
                content.append(prompt)
                
                response = model.generate_content(content)
                clean_text = response.text.strip()
                if "```json" in clean_text:
                    clean_text = clean_text.split("```json")[1].split("```")[0].strip()
                
                ai_result = json.loads(clean_text)
                
                # บันทึกลง Supabase
                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
                payload = {
                    "store_name": store_name, "customer_contact": customer_contact,
                    "raw_complaint": raw_complaint, "ai_category": ai_result['category'],
                    "churn_risk_score": ai_result['churn_risk'], "ai_elaborated_summary": ai_result['elaborated_summary'],
                    "source": "Online_Portal"
                }
                res = requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                
                if res.status_code in [200, 201]:
                    st.success(f"🎉 วิเคราะห์เคสร้าน {store_name} สำเร็จ! (ใช้รุ่น: {selected_model_name})")
                    st.balloons()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")

st.markdown("---")
st.header("📋 2. ตารางประวัติและการสืบค้น")
# ... (ส่วนตารางเหมือนเดิม)

# เพิ่มส่วนนี้เพื่อให้โชว์ผลลัพธ์บนหน้าจอทันที
                st.subheader("🤖 ผลการวิเคราะห์จาก AI")
                st.write(f"**หมวดหมู่:** {ai_result['category']}")
                st.write(f"**ความเสี่ยง (1-5):** {ai_result['churn_risk']}")
                st.info(f"**สรุป:** {ai_result['elaborated_summary']}")
                
                # ส่วนบันทึกลง Supabase เดิม...
                res = requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
