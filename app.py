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
st.header("📥 1. บันทึกเคสใหม่ (รองรับภาพและวิดีโอ)")
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
        with st.spinner("AI กำลังวิเคราะห์ข้อมูล..."):
            try:
                genai.configure(api_key=gemini_key)
                # ค้นหารุ่นอัตโนมัติ
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel('gemini-1.5-flash' if 'models/gemini-1.5-flash' in available_models else available_models[0])
                
                content = [f"วิเคราะห์ปัญหาของลูกค้า StoreHub: {raw_complaint}"]
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        if uploaded_file.type.startswith('image'):
                            img = Image.open(uploaded_file)
                            content.append(img)
                
                content.append("ตอบเป็น JSON ภาษาไทย: {category, churn_risk(1-5), elaborated_summary}")
                
                response = model.generate_content(content)
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                ai_result = json.loads(clean_text)
                
                # --- แสดงผลบนหน้าจอทันที ---
                st.success("✨ วิเคราะห์สำเร็จ!")
                st.subheader("🤖 AI Insights")
                st.write(f"**หมวดหมู่:** {ai_result['category']}")
                st.write(f"**ความเสี่ยง:** {ai_result['churn_risk']}/5")
                st.info(f"**สรุปเชิงเทคนิค:** {ai_result['elaborated_summary']}")
                
                # --- บันทึกลง Supabase ---
                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
                payload = {
                    "store_name": store_name, "customer_contact": customer_contact,
                    "raw_complaint": raw_complaint, "ai_category": ai_result['category'],
                    "churn_risk_score": ai_result['churn_risk'], "ai_elaborated_summary": ai_result['elaborated_summary'],
                    "source": "Production_Portal"
                }
                requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                st.balloons()
                
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {str(e)}")

st.markdown("---")
st.header("📋 2. ตารางประวัติ (รีเฟรชหน้าเว็บเพื่อดูข้อมูลล่าสุด)")
if supabase_url and supabase_key:
    try:
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        res = requests.get(f"{supabase_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc", headers=headers)
        if res.status_code == 200:
            st.dataframe(pd.DataFrame(res.json())[['created_at', 'store_name', 'ai_category', 'churn_risk_score', 'ai_elaborated_summary']], use_container_width=True)
    except:
        pass
