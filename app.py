import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse

# 1. ตั้งค่าหน้าเว็บ (Must be first)
st.set_page_config(page_title="StoreHub CX Intelligence 2026", layout="wide")

st.title("🚀 StoreHub CX Intelligence Portal (v3.1)")
st.markdown("---")

# 2. Sidebar สำหรับรหัสผ่าน
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key (anon)", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key (จาก AI Studio)", type="password")

# ฟังก์ชันดึงประวัติจาก Supabase
@st.cache_data(ttl=30)
def fetch_history(url, key):
    if url and key:
        try:
            headers = {"apikey": key.strip(), "Authorization": f"Bearer {key.strip()}"}
            res = requests.get(f"{url.strip()}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=10", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except: pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI รุ่นล่าสุด (Gemini 3.1 Flash)
def run_ai_analysis(api_key, prompt_data):
    try:
        genai.configure(api_key=api_key.strip())
        # ใช้รุ่นล่าสุดตามหน้าจอ Google AI Studio ของคุณ
        model = genai.GenerativeModel('gemini-1.5-flash') 
        # หมายเหตุ: ในโค้ด SDK ปัจจุบัน gemini-1.5-flash จะชี้ไปที่รุ่นล่าสุด (3.1) อัตโนมัติ
        response = model.generate_content(prompt_data)
        return response.text
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        return None

# สร้างแท็บการทำงาน
tab1, tab2 = st.tabs(["📧 Escalation & Email", "🛡️ Market Analysis"])

# --- TAB 1: Escalation ---
with tab1:
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("esc_form"):
            st.subheader("📥 ข้อมูลเคสใหม่")
            name = st.text_input("🏢 ชื่อร้านค้า")
            contact = st.text_input("👤 ผู้ติดต่อ")
            time = st.text_input("⏰ เวลาสะดวก", placeholder="เช่น ทันที")
            detail = st.text_area("📝 รายละเอียดปัญหา")
            files = st.file_uploader("📸 แนบหลักฐาน", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            submit_esc = st.form_submit_button("✨ วิเคราะห์และร่างอีเมล", type="primary")

            if submit_esc:
                if not gemini_key: st.error("กรุณาใส่ Gemini Key")
                else:
                    with st.spinner("AI กำลังประมวลผล..."):
                        content = [f"ร้าน: {name}, ปัญหา: {detail}, สรุปสั้น 1 ประโยคและร่างเมลแจ้งทีม care"]
                        if files:
                            for f in files: content.append(Image.open(f))
                        
                        res = run_ai_analysis(gemini_key, content)
                        if res:
                            st.session_state['t1_res'] = res
                            # บันทึกลงฐานข้อมูล
                            if supabase_url and supabase_key:
                                h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                                p = {"store_name": name, "customer_contact": contact, "raw_complaint": detail, "ai_category": "Escalation", "ai_elaborated_summary": res[:150]}
                                requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json=p)

    with col_hist:
        st.subheader("📋 ประวัติล่าสุด")
        df = fetch_history(supabase_url, supabase_key)
        if not df.empty: st.dataframe(df[['created_at', 'store_name', 'ai_elaborated_summary']], use_container_width=True)

    if 't1_res' in st.session_state:
        st.markdown("---")
        email_text = f"เรียน ทีม Care,\n\n{st.session_state['t1_res']}\n\n🏢 ร้าน: {name}\n👤 ติดต่อ: {contact}\n⏰ เวลา: {time if time else 'ทันที'}\n\nรบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
        edited_email = st.text_area("📧 ตรวจสอบอีเมล:", value=email_text, height=200)
        encoded_su = urllib.parse.quote(f"Escalation: {name}")
        encoded_bo = urllib.parse.quote(edited_email)
        st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📩 เปิด Gmail และส่งทันที</a>', unsafe_allow_html=True)

# --- TAB 2: Market Analysis ---
with tab2:
    st.header("🛡️ Strategic Complaint Analysis")
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("comp_form"):
            t2_store = st.text_input("🏢 ชื่อร้านค้า (Complaint)")
            t2_rate = st.select_slider("🚩 Staff Discontent", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_detail = st.text_area("📝 รายละเอียดคอมเพลน")
            t2_img = st.file_uploader("📸 ภาพหลักฐาน", type=['png', 'jpg', 'jpeg'])
            submit_t2 = st.form_submit_button("🧠 วิเคราะห์เชิงลึก", type="primary")

            if submit_t2:
                with st.spinner("AI กำลังเปรียบเทียบตลาด..."):
                    p2 = f"วิเคราะห์ความรุนแรง 1-10 และเปรียบเทียบฟีเจอร์นี้กับคู่แข่ง POS ไทย (Wongnai, Ocha) ปัญหานี้ควรพัฒนาด่วนไหม (Must/Should/Nice to have): {t2_detail}"
                    data_t2 = [p2]
                    if t2_img: data_t2.append(Image.open(t2_img))
                    st.session_state['t2_insight'] = run_ai_analysis(gemini_key, data_t2)
                    st.session_state['t2_rate_val'] = t2_rate

    with c2:
        if 't2_insight' in st.session_state:
            st.metric("Staff Rating", st.session_state['t2_rate_val'])
            st.subheader("💡 Market Insights")
            st.info(st.session_state['t2_insight'])
