import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse

st.set_page_config(page_title="StoreHub CX Intelligence", layout="wide")

st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 1. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงข้อมูลจาก Supabase
def fetch_supabase_history():
    if supabase_url and supabase_key:
        try:
            clean_url = supabase_url.strip()
            clean_skey = supabase_key.strip()
            headers = {"apikey": clean_skey, "Authorization": f"Bearer {clean_skey}"}
            res = requests.get(f"{clean_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=15", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except:
            pass
    return pd.DataFrame()

# ฟังก์ชันกลางสำหรับเรียกใช้ AI พร้อมระบบ Fallback ป้องกัน Error 404
def call_gemini_ai(prompt_content):
    gkey = gemini_key.strip()
    genai.configure(api_key=gkey)
    # ลำดับโมเดลที่ต้องการใช้ (ถ้าตัวแรก 404 จะไปตัวถัดไป)
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt_content)
            return response.text
        except Exception as e:
            if "404" in str(e):
                continue
            raise e
    raise Exception("ไม่สามารถเชื่อมต่อโมเดล AI ได้ กรุณาเช็ค API Key")

tab1, tab2 = st.tabs(["📧 Ticket & Email Escalation", "🛡️ Complaint Analysis & Market Strategy"])

# --- TAB 1: Ticket & Email Escalation ---
with tab1:
    st.header("🎟️ Escalation Tool")
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.container(border=True):
            st.subheader("📥 ข้อมูลเคสใหม่")
            t1_store = st.text_input("🏢 ชื่อร้านค้า", key="store_t1")
            t1_contact = st.text_input("👤 ผู้ติดต่อ", key="contact_t1")
            t1_time = st.text_input("⏰ เวลาสะดวก", placeholder="เช่น ทันที", key="time_t1")
            t1_raw = st.text_area("📝 รายละเอียดปัญหา", height=100, key="raw_t1")
            t1_files = st.file_uploader("📸 แนบหลักฐาน", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="files_t1")
            
            if st.button("✨ วิเคราะห์ & ร่างอีเมล", type="primary", key="btn_t1"):
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังสรุปเคส..."):
                        try:
                            prompt = f"สรุปปัญหาร้าน {t1_store} สั้นๆ 1 ประโยค และร่างอีเมลประสานงานจากข้อมูลนี้: {t1_raw}"
                            ai_response = call_gemini_ai(prompt)
                            st.session_state['t1_ready'] = True
                            st.session_state['t1_result'] = ai_response
                            
                            # บันทึกลง Supabase
                            if supabase_url and supabase_key:
                                headers = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                                payload = {"store_name": t1_store, "customer_contact": t1_contact, "raw_complaint": t1_raw, "ai_category": "Escalation", "churn_risk_score": 3, "ai_elaborated_summary": ai_response[:100]}
                                requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                        except Exception as e: st.error(f"Error: {str(e)}")

        if st.session_state.get('t1_ready'):
            with st.container(border=True):
                st.subheader("📩 เทมเพลตอีเมล")
                mail_body = f"เรียน ทีม Care,\n\n{st.session_state['t1_result']}\n\n🏢 ชื่อร้าน: {t1_store}\n👤 ผู้ติดต่อ: {t1_contact}\n⏰ เวลาติดต่อ: {t1_time if t1_time else 'ติดต่อทันที'}\n\nรบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
                edited_mail = st.text_area("แก้ไขเนื้อหา:", value=mail_body, height=150)
                encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
                encoded_bo = urllib.parse.quote(edited_mail)
                gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}"
                st.markdown(f'<a href="{gmail_url}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📩 เปิด Gmail ส่งทันที</a>', unsafe_allow_html=True)

    with col2:
        st.subheader("📋 ประวัติล่าสุด")
        df_history = fetch_supabase_history()
        if not df_history.empty: st.dataframe(df_history[['created_at', 'store_name', 'ai_elaborated_summary']], use_container_width=True, height=400)

# --- TAB 2: Complaint Analysis & Strategy ---
with tab2:
    st.header("🛡️ Deep Analysis")
    c_in, c_out = st.columns([1, 1])
    with c_in:
        with st.container(border=True):
            st.subheader("📥 บันทึก Complaints")
            t2_store = st.text_input("🏢 ชื่อร้านค้า", key="store_t2")
            t2_staff_rating = st.select_slider("🚩 Staff Rating", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียดคอมเพลน", height=100, key="raw_t2")
            t2_file = st.file_uploader("📸 หลักฐาน", type=['png', 'jpg', 'jpeg'], key="file_t2")
            
            if st.button("🧠 วิเคราะห์กลยุทธ์", type="primary", key="btn_t2"):
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังวิเคราะห์ตลาด..."):
                        try:
                            analysis_prompt = f"วิเคราะห์ข้อร้องเรียนนี้เทียบกับคู่แข่ง POS ในไทย: '{t2_raw}' ให้คะแนนความรุนแรง 1-10 และสรุปความสำคัญที่ควรพัฒนาฟีเจอร์ (Must/Should/Nice to have) สั้นๆ"
                            content = [analysis_prompt]
                            if t2_file: content.append(Image.open(t2_file))
                            st.session_state['t2_insight'] = call_gemini_ai(content)
                            st.session_state['t2_ai_score'] = "8/10" if t2_staff_rating in ["สูง", "วิกฤต"] else "4/10"
                        except Exception as e: st.error(f"Error AI: {str(e)}")

    with c_out:
        st.subheader("💡 Strategic Insights")
        if st.session_state.get('t2_insight'):
            st.metric("Staff Rating", t2_staff_rating)
            st.metric("AI Severity", st.session_state['t2_ai_score'])
            st.info(st.session_state['t2_insight'])
