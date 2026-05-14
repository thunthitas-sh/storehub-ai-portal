import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse

# 1. ตั้งค่าหน้าเว็บ (ต้องเป็นคำสั่งแรกสุด)
st.set_page_config(page_title="StoreHub CX Intelligence 2026", layout="wide")

st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงประวัติจาก Supabase
@st.cache_data(ttl=30)
def fetch_history(url, key):
    if url and key:
        try:
            headers = {"apikey": key.strip(), "Authorization": f"Bearer {key.strip()}"}
            res = requests.get(f"{url.strip()}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=10", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except:
            pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI แบบเสถียร (แก้ปัญหา 404 โดยใช้รุ่นมาตรฐาน)
def run_ai_analysis(api_key, prompt_data):
    try:
        genai.configure(api_key=api_key.strip())
        # ใช้รุ่นมาตรฐานที่ Google รองรับในปัจจุบัน
        model = genai.GenerativeModel('gemini-pro') 
        response = model.generate_content(prompt_data)
        return response.text
    except Exception as e:
        # หาก gemini-pro ไม่รองรับภาพ ให้ลอง fallback ไปที่รุ่นล่าสุด
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(prompt_data)
            return response.text
        except:
            st.error(f"❌ AI Error: {str(e)}")
            return None

# สร้าง Tabs
tab1, tab2 = st.tabs(["📧 Escalation Tool", "🛡️ Strategic Analysis"])

# --- TAB 1: Escalation & Email ---
with tab1:
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("esc_form"):
            st.subheader("📥 บันทึกเคสใหม่")
            name = st.text_input("🏢 ชื่อร้านค้า")
            contact = st.text_input("👤 ผู้ติดต่อ")
            time = st.text_input("⏰ เวลาสะดวก", placeholder="เช่น ทันที")
            detail = st.text_area("📝 รายละเอียดปัญหา")
            files = st.file_uploader("📸 แนบภาพ", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            submit_esc = st.form_submit_button("✨ วิเคราะห์และร่างอีเมล", type="primary")

            if submit_esc:
                if not gemini_key:
                    st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังทำงาน..."):
                        content = [f"สรุปปัญหาร้าน {name} สั้นๆ 1 ประโยค และร่างอีเมลแจ้งทีม care จากข้อมูล: {detail}"]
                        if files:
                            for f in files:
                                content.append(Image.open(f))
                        
                        res = run_ai_analysis(gemini_key, content)
                        if res:
                            st.session_state['t1_res'] = res
                            # บันทึกลง Supabase
                            if supabase_url and supabase_key:
                                h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                                p = {"store_name": name, "customer_contact": contact, "raw_complaint": detail, "ai_category": "Escalation", "ai_elaborated_summary": res[:150]}
                                requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json=p)

    with col_hist:
        st.subheader("📋 ประวัติล่าสุด")
        df = fetch_history(supabase_url, supabase_key)
        if not df.empty:
            st.dataframe(df[['created_at', 'store_name', 'ai_elaborated_summary']], use_container_width=True)

    if 't1_res' in st.session_state:
        st.markdown("---")
        final_mail = f"เรียน ทีม Care,\n\n{st.session_state['t1_res']}\n\n🏢 ชื่อร้าน: {name}\n👤 ผู้ติดต่อ: {contact}\n⏰ เวลาติดต่อ: {time if time else 'ทันที'}\n\nรบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
        edited_email = st.text_area("📧 ตรวจสอบอีเมล:", value=final_mail, height=200)
        encoded_su = urllib.parse.quote(f"Escalation: {name}")
        encoded_bo = urllib.parse.quote(edited_email)
        st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📩 เปิด Gmail ส่งทันที</a>', unsafe_allow_html=True)

# --- TAB 2: Market Analysis ---
with tab2:
    st.header("🛡️ วิเคราะห์ Complaints เชิงลึก")
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("comp_form"):
            t2_store = st.text_input("🏢 ชื่อบัญชีร้านค้า")
            t2_rate = st.select_slider("🚩 ทีมเรทความไม่พอใจ", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_detail = st.text_area("📝 รายละเอียด (พิมพ์หรือแคปภาพ)")
            t2_img = st.file_uploader("📸 หลักฐาน", type=['png', 'jpg', 'jpeg'])
            submit_t2 = st.form_submit_button("🧠 วิเคราะห์กลยุทธ์", type="primary")

            if submit_t2:
                with st.spinner("AI กำลังเปรียบเทียบตลาด..."):
                    p2 = f"วิเคราะห์ความรุนแรง (1-10) และเปรียบเทียบฟีเจอร์นี้กับคู่แข่ง POS ในไทย ปัญหานี้ควรพัฒนาด่วนแค่ไหน (Must/Should/Nice to have): {t2_detail}"
                    data_t2 = [p2]
                    if t2_img:
                        data_t2.append(Image.open(t2_img))
                    st.session_state['t2_insight'] = run_ai_analysis(gemini_key, data_t2)
                    st.session_state['t2_rate_val'] = t2_rate

    with c2:
        if 't2_insight' in st.session_state:
            st.metric("Staff Rating", st.session_state['t2_rate_val'])
            st.subheader("💡 Market Insights")
            st.info(st.session_state['t2_insight'])
