import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="StoreHub CX Intelligence", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 StoreHub CX Intelligence Portal")

# 1. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงข้อมูลจาก Supabase
def fetch_data():
    if supabase_url and supabase_key:
        try:
            headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
            res = requests.get(f"{supabase_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=20", headers=headers)
            return pd.DataFrame(res.json()) if res.status_code == 200 else pd.DataFrame()
        except: return pd.DataFrame()
    return pd.DataFrame()

# สร้าง Tabs
tab1, tab2 = st.tabs(["📧 Ticket & Email Escalation", "🛡️ Complaint Analysis & Market Strategy"])

# --- TAB 1: Ticket & Email Escalation ---
with tab1:
    st.header("🎟️ Escalation Tool")
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container(border=True):
            st.subheader("📥 ข้อมูลเคสใหม่")
            store_name = st.text_input("🏢 ชื่อร้านค้า", key="t1_store")
            customer_contact = st.text_input("👤 ผู้ติดต่อ", key="t1_contact")
            contact_time = st.text_input("⏰ เวลาสะดวก", placeholder="เช่น ทันที", key="t1_time")
            raw_complaint = st.text_area("📝 รายละเอียดปัญหา", height=100, key="t1_raw")
            uploaded_files = st.file_uploader("📸 แนบหลักฐาน", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="t1_files")
            
            if st.button("✨ วิเคราะห์ & ร่างอีเมล", type="primary"):
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("กำลังสรุปเคส..."):
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"สรุปเคสนี้สั้นๆ และร่างอีเมลแจ้งทีม care: {raw_complaint} ร้าน {store_name}"
                        response = model.generate_content(prompt)
                        st.session_state['t1_result'] = response.text
                        st.balloons()

    with col2:
        st.subheader("📋 ประวัติเคสล่าสุด")
        df_history = fetch_data()
        if not df_history.empty:
            st.dataframe(df_history[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']], height=400)
        else:
            st.info("ไม่พบประวัติข้อมูล")

    if 't1_result' in st.session_state:
        st.markdown("---")
        st.subheader("📧 Email Preview & Action")
        edited_mail = st.text_area("ร่างอีเมล (แก้ไขได้):", value=st.session_state['t1_result'], height=200)
        encoded_subject = urllib.parse.quote(f"Escalation: {store_name}")
        encoded_body = urllib.parse.quote(edited_mail + "\n\nรบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม")
        gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_subject}&body={encoded_body}"
        st.markdown(f'<a href="{gmail_link}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📩 เปิด Gmail ส่งทันที</a>', unsafe_allow_html=True)

# --- TAB 2: Complaint Analysis & Market Strategy ---
with tab2:
    st.header("🛡️ Deep Complaint Analysis")
    st.markdown("วิเคราะห์ระดับความรุนแรงและโอกาสในการพัฒนาฟีเจอร์เมื่อเทียบกับคู่แข่ง")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            comp_store = st.text_input("🏢 ชื่อบัญชีร้านค้า", key="t2_store")
            staff_rating = st.select_slider("🚩 ทีมเรทความไม่พอใจ (Staff Rating)", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
        with c2:
            comp_detail = st.text_area("📝 รายละเอียด Complaints (พิมพ์หรือแคปภาพ)", height=100, key="t2_detail")
            comp_files = st.file_uploader("📸 แนบภาพหลักฐานปัญหา", type=['png', 'jpg', 'jpeg'], key="t2_files")

        if st.button("🧠 วิเคราะห์เชิงกลยุทธ์", type="primary"):
            with st.spinner("AI กำลังเปรียบเทียบข้อมูลตลาด..."):
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                analysis_prompt = f"""วิเคราะห์ Complaint นี้: {comp_detail} 
                1. เรทดีกรีความรุนแรง (1-10) 
                2. เปรียบเทียบฟีเจอร์นี้กับคู่แข่ง (POS ตลาดไทย) 
                3. สรุปว่านี่คือฟีเจอร์ที่ 'ควรทำมากแค่ไหน' (Must-have / Should-have / Nice-to-have)
                ตอบเป็นภาษาไทย สั้น กระชับ เป็นข้อๆ"""
                
                content = [analysis_prompt]
                if comp_files: content.append(Image.open(comp_files))
                
                res = model.generate_content(content)
                
                # แสดงผล Analysis
                st.markdown("---")
                res_c1, res_c2 = st.columns([1, 2])
                with res_c1:
                    st.metric("AI Severity Score", "8/10" if "วิกฤต" in staff_rating else "5/10")
                    st.warning(f"Staff Rating: {staff_rating}")
                with res_c2:
                    st.subheader("📊 Market Strategy Insight")
                    st.write(res.text)

    st.info("💡 ข้อมูลในหน้านี้จะช่วยให้ Product Team ตัดสินใจได้ว่าเคสไหนควรเป็น Priority ในการพัฒนา Roadmap")
