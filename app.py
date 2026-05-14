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
    # ปรับให้รับหลายไฟล์ (accept_multiple_files=True)
    uploaded_files = st.file_uploader("📸 แนบหลักฐาน (เลือกได้หลายไฟล์ภาพหรือวิดีโอ)", 
                                    type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], 
                                    accept_multiple_files=True)

with col2:
    raw_complaint = st.text_area("ข้อความแจ้งปัญหาเบื้องต้น", height=150)

if st.button("✨ ส่งข้อมูลและให้ AI ประมวลผล", type="primary"):
    if not (supabase_url and supabase_key and gemini_key):
        st.error("❌ กรุณากรอกข้อมูล Keys ให้ครบถ้วน")
    else:
        with st.spinner("AI กำลังวิเคราะห์ข้อมูลและไฟล์แนบทั้งหมด..."):
            try:
                genai.configure(api_key=gemini_key)
                
                # แผนแก้ 404 ขั้นเด็ดขาด: ให้ AI ลองหาชื่อรุ่นที่เครื่องนี้รู้จัก
                model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
                model = None
                
                for name in model_names:
                    try:
                        model = genai.GenerativeModel(name)
                        # ทดสอบส่งข้อความสั้นๆ เพื่อเช็คว่ารุ่นนี้ใช้ได้จริงไหม
                        model.generate_content("test") 
                        break 
                    except:
                        continue
                
                if model is None:
                    st.error("❌ เครื่องนี้ไม่รู้จักชื่อรุ่น Gemini เลย กรุณาเช็คอินเทอร์เน็ตหรือ API Key")
                    st.stop()

                
                content = [f"วิเคราะห์ปัญหานี้ของลูกค้า StoreHub: {raw_complaint}"]
                
                # จัดการกับหลายไฟล์
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if uploaded_file.type.startswith('image'):
                            img = Image.open(uploaded_file)
                            content.append(img)
                        else:
                            content.append(f"[ไฟล์วิดีโอแนบมาชื่อ: {uploaded_file.name}]")

                prompt = """วิเคราะห์รูปภาพและข้อความ แล้วตอบเป็น JSON ภาษาไทยเท่านั้น:
                {
                  "category": "Hardware/Software/Payment/UserError",
                  "churn_risk": 1-5,
                  "elaborated_summary": "สรุปอาการเชิงเทคนิคจากรูปและข้อความ พร้อมวิธีแก้"
                }"""
                content.append(prompt)
                
                response = model.generate_content(content)
                # ล้างค่าเพื่อให้เป็น JSON ที่ถูกต้อง
                clean_text = response.text.strip()
                if "```json" in clean_text:
                    clean_text = clean_text.split("```json")[1].split("```")[0].strip()
                
                ai_result = json.loads(clean_text)
                
                # บันทึกลง Supabase
                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
                payload = {
                    "store_name": store_name, 
                    "customer_contact": customer_contact,
                    "raw_complaint": raw_complaint, 
                    "ai_category": ai_result['category'],
                    "churn_risk_score": ai_result['churn_risk'], 
                    "ai_elaborated_summary": ai_result['elaborated_summary'],
                    "source": "Onboarding_Portal_MultiFile"
                }
                res = requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                
                if res.status_code in [200, 201]:
                    st.success(f"🎉 วิเคราะห์เคสร้าน {store_name} สำเร็จ! ข้อมูลถูกส่งเข้าฐานข้อมูลแล้ว")
                    st.balloons()
                else:
                    st.error(f"Error บันทึกข้อมูล: {res.text}")
                    
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")
                st.info("คำแนะนำ: หากยังขึ้น 404 ให้ลองตรวจสอบว่า Gemini Key ของคุณเปิดใช้งานในโปรเจกต์ที่ถูกต้องหรือไม่")

st.markdown("---")
st.header("📋 2. ตารางประวัติและการสืบค้น")
# ... (ส่วนตารางเหมือนเดิม)
if supabase_url and supabase_key:
    try:
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        res = requests.get(f"{supabase_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc", headers=headers)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                st.dataframe(df[['created_at', 'store_name', 'ai_category', 'churn_risk_score', 'ai_elaborated_summary']], use_container_width=True)
    except:
        pass