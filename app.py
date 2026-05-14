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

# ฟังก์ชันดึงข้อมูลจาก Supabase ที่ปลอดภัย
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

# สร้าง Tabs 2 ฝั่งตามฟังก์ชันที่ต้องการ
tab1, tab2 = st.tabs(["📧 Ticket & Email Escalation", "🛡️ Complaint Analysis & Market Strategy"])

# ==========================================
# --- TAB 1: Ticket & Email Escalation ---
# ==========================================
with tab1:
    st.header("🎟️ เปิดทิคเก็ตใหม่ & ร่างอีเมลแจ้งทีม Care")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("📥 กรอกรายละเอียดเคส")
            t1_store = st.text_input("🏢 ชื่อร้านค้า", key="store_t1")
            t1_contact = st.text_input("👤 ผู้ติดต่อ / เบอร์โทร", key="contact_t1")
            t1_time = st.text_input("⏰ เวลาที่สะดวกให้ติดต่อ", placeholder="เช่น ทันที", key="time_t1")
            t1_raw = st.text_area("📝 รายละเอียดเคส", placeholder="กรอกปัญหาที่พบ...", height=120, key="raw_t1")
            t1_files = st.file_uploader("📸 แนบหลักฐาน (ภาพ)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="files_t1")

            if st.button("✨ ประมวลผลและร่างอีเมล", type="primary", key="btn_t1"):
                if not gemini_key:
                    st.error("❌ กรุณากรอก Gemini API Key ที่แถบซ้ายมือ")
                else:
                    with st.spinner("AI กำลังสรุปข้อมูล..."):
                        try:
                            gkey = gemini_key.strip()
                            genai.configure(api_key=gkey)
                            
                            # เปลี่ยนเป็น 'gemini-pro' รุ่นเสถียรถาวรเพื่อแก้ปัญหา 404 บล็อกนี้
                            model = genai.GenerativeModel('gemini-pro')
                            
                            prompt = f"สรุปปัญหานี้สั้นๆ เป็นประโยคเดียวคมๆ และร่างเนื้อหาอีเมลเพื่อประสานงานต่อจากข้อความนี้: {t1_raw}"
                            response = model.generate_content(prompt)
                            
                            st.session_state['t1_ready'] = True
                            st.session_state['t1_subject'] = f"Escalation: {t1_store}"
                            st.session_state['t1_email_body'] = (
                                f"เรียน ทีม Care,\n\nรายละเอียดเคส: {response.text}\n\n"
                                f"🏢 ชื่อร้าน: {t1_store}\n👤 ผู้ติดต่อ: {t1_contact}\n⏰ เวลาติดต่อ: {t1_time if t1_time else 'ติดต่อทันที'}\n\n"
                                f"รบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
                            )
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {str(e)}")

        if st.session_state.get('t1_ready'):
            with st.container(border=True):
                u_subject = st.text_input("หัวข้ออีเมลอัตโนมัติ:", value=st.session_state['t1_subject'])
                u_body = st.text_area("เนื้อหาอีเมล (ปรับแก้เพิ่มได้):", value=st.session_state['t1_email_body'], height=200)
                
                encoded_su = urllib.parse.quote(u_subject)
                encoded_bo = urllib.parse.quote(u_body)
                gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}"
                st.markdown(f'<a href="{gmail_url}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📬 กดเพื่อเปิด Gmail และส่งทันที</a>', unsafe_allow_html=True)

    with col2:
        st.subheader("📋 ประวัติเคสล่าสุด")
        df_t1 = fetch_supabase_history()
        if not df_t1.empty:
            st.dataframe(df_t1[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']], use_container_width=True, height=450)

# ==========================================
# --- TAB 2: Complaint Analysis & Strategy ---
# ==========================================
with tab2:
    st.header("🛡️ บันทึก Complaints & วิเคราะห์เชิงฟีเจอร์และคู่แข่งตลาด")
    col_input, col_insight = st.columns([1, 1])
    
    with col_input:
        with st.container(border=True):
            st.subheader("📥 บันทึกข้อมูล Complaints")
            t2_store = st.text_input("🏢 ชื่อบัญชีร้านค้า", key="store_t2")
            t2_staff_rating = st.select_slider("🚩 ทีมเรทความไม่พอใจของลูกค้า", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียดคอมเพลนดิบ", placeholder="กรอกคอมเพลน...", height=120, key="raw_t2")
            t2_file = st.file_uploader("📸 อัปโหลดภาพคอมเพลน", type=['png', 'jpg', 'jpeg'], key="file_t2")
            
            if st.button("🧠 วิเคราะห์วิสัยทัศน์ตลาดและบันทึก", type="primary", key="btn_t2"):
                if not gemini_key:
                    st.error("❌ กรุณากรอก Gemini API Key")
                else:
                    with st.spinner("AI กำลังเปรียบเทียบฟีเจอร์กับคู่แข่ง..."):
                        try:
                            gkey = gemini_key.strip()
                            genai.configure(api_key=gkey)
                            
                            # เปลี่ยนเป็นรุ่น 'gemini-pro' เพื่อความเสถียรสูงสุดในบล็อกนี้เช่นกัน
                            model = genai.GenerativeModel('gemini-pro')
                            
                            analysis_prompt = (
                                "คุณคือผู้เชี่ยวชาญด้านกลยุทธ์ผลิตภัณฑ์ POS ในตลาดประเทศไทย "
                                "جงวิเคราะห์ข้อร้องเรียนนี้: '" + str(t2_raw) + "' "
                                "ให้ตอบกลับมาเป็นข้อๆ อย่างสั้น กระชับ และตรงประเด็นที่สุด ย่อหน้าละ 1 ประโยคเท่านั้น: "
                                "1. AI Severity Rating: ประเมินดีกรีความรุนแรง คะแนนเป็น 1-10 พร้อมเหตุผลสั้นๆ "
                                "2. Market Comparison: เมื่อเทียบกับคู่แข่งในไทย เช่น Wongnai POS, Ocha, FoodStory ฟีเจอร์นี้เราเสียเปรียบไหม? "
                                "3. Feature Priority: ความจำเป็นในการพัฒนาฟีเจอร์นี้ ระดับ Must-have / Should-have / Nice-to-have เพราะอะไร?"
                            )
                            
                            content = [analysis_prompt]
                            if t2_file:
                                content.append(Image.open(t2_file))
                                
                            response = model.generate_content(content)
                            st.session_state['t2_insight'] = response.text
                            st.session_state['t2_ai_rating'] = "8/10" if t2_staff_rating in ["สูง", "วิกฤต"] else "4/10"
                            
                            # บันทึกลง Supabase
                            if supabase_url and supabase_key:
                                curl = supabase_url.strip()
                                cskey = supabase_key.strip()
                                headers = {"apikey": cskey, "Authorization": f"Bearer {cskey}", "Content-Type": "application/json"}
                                payload = {
                                    "store_name": t2_store, "customer_contact": f"Staff: {t2_staff_rating}",
                                    "raw_complaint": t2_raw, "ai_category": "Market_Complaint",
                                    "churn_risk_score": 5 if t2_staff_rating == "วิกฤต" else 3, 
                                    "ai_elaborated_summary": response.text[:200]
                                }
                                requests.post(f"{curl}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                                st.session_state['t2_saved'] = True
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดในระบบ AI: {str(e)}")

    with col_insight:
        st.subheader("💡 AI Insights & ตลาดเชิงกลยุทธ์")
        if st.session_state.get('t2_insight'):
            if st.session_state.get('t2_saved'):
                st.success("💾 บันทึกข้อมูลลงฐานข้อมูลสำเร็จแล้ว!")
            
            r_c1, r_c2 = st.columns(2)
            with r_c1: st.metric("Staff Rating", t2_staff_rating)
            with r_c2: st.metric("AI Severity", st.session_state['t2_ai_rating'])
                
            st.markdown("---")
            st.markdown("**📌 บทวิเคราะห์เชิงกลยุทธ์ฟีเจอร์:**")
            st.write(st.session_state['t2_insight'])
        else:
            st.info("💡 กรอกข้อมูลคอมเพลนและกดวิเคราะห์ที่ฝั่งซ้ายเพื่อดูผลลัพธ์")
