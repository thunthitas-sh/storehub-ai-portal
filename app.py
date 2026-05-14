import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse

# ตั้งค่าหน้ากระดาษเป็นอันดับแรก
st.set_page_config(page_title="StoreHub CX Intelligence", layout="wide")

st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 1. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงข้อมูลจาก Supabase (ดึงเมื่อจำเป็นเท่านั้นเพื่อลดการค้าง)
@st.cache_data(ttl=60)
def fetch_supabase_history(url, key):
    if url and key:
        try:
            headers = {"apikey": key.strip(), "Authorization": f"Bearer {key.strip()}"}
            res = requests.get(f"{url.strip()}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=15", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except: pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI แบบเสถียร (ระบุรุ่นเดียวที่รองรับชัวร์เพื่อป้องกัน Loop ค้าง)
def call_gemini_ai(api_key, content_list):
    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(content_list)
    return response.text

tab1, tab2 = st.tabs(["📧 Ticket Escalation", "🛡️ Complaint Analysis"])

# --- TAB 1: Escalation ---
with tab1:
    st.header("🎟️ Escalation Tool")
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("escalation_form"):
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_contact = st.text_input("👤 ผู้ติดต่อ")
            t1_time = st.text_input("⏰ เวลาสะดวก", placeholder="ติดต่อทันที")
            t1_raw = st.text_area("📝 รายละเอียดปัญหา")
            t1_files = st.file_uploader("📸 แนบหลักฐาน", type=['png', 'jpg', 'jpeg'])
            submitted = st.form_submit_button("✨ ประมวลผลและร่างเมล", type="primary")
            
            if submitted:
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังทำงาน..."):
                        try:
                            prompt = f"สรุปปัญหาร้าน {t1_store} สั้นๆ 1 ประโยค และร่างอีเมลประสานงาน: {t1_raw}"
                            ai_res = call_gemini_ai(gemini_key, prompt)
                            st.session_state['t1_result'] = ai_res
                            st.success("ประมวลผลเสร็จแล้ว!")
                        except Exception as e: st.error(f"Error: {str(e)}")

        if 't1_result' in st.session_state:
            mail_body = f"เรียน ทีม Care,\n\n{st.session_state['t1_result']}\n\n🏢 ร้าน: {t1_store}\n👤 ติดต่อ: {t1_contact}\n⏰ เวลา: {t1_time if t1_time else 'ทันที'}\n\nรบกวนติดต่อกลับร้านค้าเพิ่มเติม"
            st.text_area("ร่างอีเมล:", value=mail_body, height=150)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📩 เปิด Gmail ส่งทันที</a>', unsafe_allow_html=True)

    with c2:
        st.subheader("📋 ประวัติล่าสุด")
        df = fetch_supabase_history(supabase_url, supabase_key)
        if not df.empty: st.dataframe(df[['created_at', 'store_name', 'ai_elaborated_summary']], use_container_width=True)

# --- TAB 2: Complaint Analysis ---
with tab2:
    st.header("🛡️ Deep Analysis")
    ci, co = st.columns([1, 1])
    with ci:
        with st.form("complaint_form"):
            t2_store = st.text_input("🏢 ชื่อร้านค้า")
            t2_staff_rating = st.select_slider("🚩 Staff Rating", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียดคอมเพลน")
            t2_file = st.file_uploader("📸 หลักฐานภาพ", type=['png', 'jpg', 'jpeg'])
            submitted_t2 = st.form_submit_button("🧠 วิเคราะห์กลยุทธ์", type="primary")
            
            if submitted_t2:
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังวิเคราะห์..."):
                        try:
                            p2 = f"วิเคราะห์ข้อร้องเรียนนี้เทียบกับคู่แข่ง POS ในไทย: '{t2_raw}' ให้คะแนนความรุนแรง 1-10 และสรุปฟีเจอร์ที่ควรพัฒนาสั้นๆ"
                            content = [p2]
                            if t2_file: content.append(Image.open(t2_file))
                            st.session_state['t2_insight'] = call_gemini_ai(gemini_key, content)
                            st.session_state['t2_staff_val'] = t2_staff_rating
                        except Exception as e: st.error(f"Error: {str(e)}")

    with co:
        if 't2_insight' in st.session_state:
            st.subheader("💡 Strategic Insights")
            st.metric("Staff Rating", st.session_state['t2_staff_val'])
            st.info(st.session_state['t2_insight'])
