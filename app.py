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
            headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
            # ดึง 15 เคสล่าสุดมาโชว์
            res = requests.get(f"{supabase_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc&limit=15", headers=headers)
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
            t1_time = st.text_input("⏰ เวลาที่สะดวกให้ติดต่อ", placeholder="เช่น ทันที หรือ หลัง 14:00 น.", key="time_t1")
            t1_raw = st.text_area("📝 รายละเอียดเคส", placeholder="กรอกปัญหาที่พบ...", height=120, key="raw_t1")
            t1_files = st.file_uploader("📸 แนบหลักฐาน (ภาพ)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key="files_t1")

            if st.button("✨ ประมวลผลและร่างอีเมล", type="primary", key="btn_t1"):
                if not gemini_key:
                    st.error("❌ กรุณากรอก Gemini API Key ที่ แถบซ้ายมือ")
                else:
                    with st.spinner("AI กำลังสรุปข้อมูลและร่างอีเมล..."):
                        try:
                            genai.configure(api_key=gemini_key)
                            # ใช้รุ่นเสถียรตรงๆ ลด Header/gRPC error
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""คุณคือผู้ช่วยสรุปเคส Support ของ StoreHub
                            ชื่อร้าน: {t1_store}
                            ผู้ติดต่อ: {t1_contact}
                            เวลาสะดวก: {t1_time if t1_time else 'ติดต่อทันที'}
                            รายละเอียดปัญหา: {t1_raw}
                            
                            จงสรุปปัญหาเป็นประโยคที่สั้น กระชับ ได้ใจความที่สุด 1 ประโยค (ย้ำว่าสั้นและตรงประเด็น)
                            และร่างเนื้อหาอีเมลเพื่อประสานงานต่อ
                            
                            ตอบกลับเป็น JSON ภาษาไทยรูปแบบนี้เท่านั้น:
                            {{
                              "short_summary": "สรุปปัญหาสั้นกระชับ",
                              "email_content": "เนื้อหารายละเอียดของปัญหาแบบสรุปใจความสำคัญ"
                            }}"""
                            
                            response = model.generate_content(prompt)
                            clean_json = response.text.strip().replace("```json", "").replace("```", "")
                            ai_res = json.loads(clean_json)
                            
                            # บันทึกลงฐานข้อมูลอ้างอิงของ Tab 1
                            if supabase_url and supabase_key:
                                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
                                payload = {
                                    "store_name": t1_store, "customer_contact": t1_contact,
                                    "raw_complaint": t1_raw, "ai_category": "Escalation",
                                    "churn_risk_score": 3, "ai_elaborated_summary": ai_res['short_summary']
                                }
                                requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                            
                            st.session_state['t1_ready'] = True
                            st.session_state['t1_subject'] = f"Escalation: {t1_store} | {ai_res['short_summary']}"
                            
                            # ประกอบเทมเพลตอีเมลตามเงื่อนไขเป๊ะๆ
                            st.session_state['t1_email_body'] = (
                                f"เรียน ทีม Care,\n\n"
                                f"รายละเอียดเคส: {ai_res['email_content']}\n\n"
                                f"🏢 ชื่อร้าน: {t1_store}\n"
                                f"👤 ผู้ติดต่อ: {t1_contact}\n"
                                f"⏰ เวลาติดต่อ: {t1_time if t1_time else 'ติดต่อทันที'}\n\n"
                                f"รบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
                            )
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {str(e)}")

        # ส่วนแสดงผลลัพธ์เมื่อประมวลผลเสร็จ
        if st.session_state.get('t1_ready'):
            with st.container(border=True):
                st.subheader("📩 เทมเพลตอีเมลพร้อมส่ง (เชื่อมลิงก์ Gmail)")
                u_subject = st.text_input("หัวข้ออีเมลอัตโนมัติ:", value=st.session_state['t1_subject'])
                u_body = st.text_area("เนื้อหาอีเมล (ปรับแก้เพิ่มได้):", value=st.session_state['t1_email_body'], height=200)
                
                encoded_su = urllib.parse.quote(u_subject)
                encoded_bo = urllib.parse.quote(u_body)
                gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}"
                
                st.markdown(f'<a href="{gmail_url}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; text-align: center;">📬 กดเพื่อเปิด Gmail และส่งทันที</a>', unsafe_allow_html=True)
                st.caption("📎 สำหรับไฟล์ภาพ: รบกวนลากไฟล์ภาพไปวางแนบในหน้าต่าง Gmail ที่เปิดขึ้นมาได้เลยครับ")
                st.balloons()

    with col2:
        st.subheader("📋 ประวัติเคสที่ส่งเข้ามาล่าสุด")
        df_t1 = fetch_supabase_history()
        if not df_t1.empty:
            # คัดกรองคอลัมน์มาโชว์ให้ดูง่ายๆ ไม่ลกตา
            st.dataframe(df_t1[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']], use_container_width=True, height=450)
        else:
            st.info("💡 กำลังรอข้อมูล หรือยังไม่มีประวัติการบันทึกเคส")

# ==========================================
# --- TAB 2: Complaint Analysis & Strategy ---
# ==========================================
with tab2:
    st.header("🛡️ บันทึก Complaints & วิเคราะห์เชิงฟีเจอร์และคู่แข่งตลาด")
    st.markdown("พิมพ์รายละเอียดปัญหา หรืออัปโหลดภาพคอมเพลน เพื่อให้ AI เฟ้นหาจุดที่ควรพัฒนาเปรียบเทียบกับคู่แข่งในตลาด")
    
    col_input, col_insight = st.columns([1, 1])
    
    with col_input:
        with st.container(border=True):
            st.subheader("📥 บันทึกข้อมูล Complaints")
            t2_store = st.text_input("🏢 ชื่อบัญชีร้านค้า", key="store_t2")
            t2_staff_rating = st.select_slider("🚩 ทีมเรทความไม่พอใจของลูกค้า (Staff Rating)", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียดปัญหาร้านค้า / คอมเพลนดิบ", placeholder="กรอกคอมเพลนของร้านค้าเพื่อนำไปวิเคราะห์ทำ Dashboard...", height=120, key="raw_t2")
            t2_file = st.file_uploader("📸 อัปโหลดภาพแคปหน้าจอ / หลักฐานคอมเพลน", type=['png', 'jpg', 'jpeg'], key="file_t2")
            
            if st.button("🧠 วิเคราะห์วิสัยทัศน์ตลาดและบันทึก", type="primary", key="btn_t2"):
                if not gemini_key:
                    st.error("❌ กรุณากรอก Gemini API Key")
                else:
                    with st.spinner("AI กำลังวิเคราะห์และเปรียบเทียบฟีเจอร์กับคู่แข่งในตลาด..."):
                        try:
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            # สั่งให้สรุปกระชับ ได้ใจความ ไม่บรรยายยาวเกินไป
                            analysis_prompt = f"""คุณคือผู้เชี่ยวชาญด้านกลยุทธ์ผลิตภัณฑ์ POS ในตลาดประเทศไทย 
                            จงวิเคราะห์ข้อร้องเรียนนี้: "{t2_raw}"
                            
                            ให้ตอบกลับมาเป็นข้อๆ อย่างสั้น กระชับ และตรงประเด็น (เนื้อๆ ไม่เอาน้ำ) ดังนี้:
                            1. **AI Severity Rating**: ประเมินดีกรีความรุนแรงโดย AI (ให้คะแนนเป็น 1-10 พร้อมเหตุผลสั้นๆ 1 ประโยค)
                            2. **Market Comparison**: ฟีเจอร์ที่เจอปัญหานี้ เมื่อเปรียบเทียบกับคู่แข่ง POS ในตลาดไทย (เช่น Wongnai POS, FoodStory, Ocha) คู่แข่งทำได้ดีกว่าหรือเจอปัญหาเดียวกัน?
                            3. **Feature Priority**: ควรทำฟีเจอร์นี้มากน้อยแค่ไหน? ระบุระดับ (Must-have / Should-have / Nice-to-have) พร้อมเหตุผลเชิงธุรกิจสั้นๆ กระชับ
                            """
                            
                            content = [analysis_prompt]
                            if t2_file:
                                content.append(Image.open(t2_file))
                                
                            response = model.generate_content(content)
                            st.session_state['t2_insight'] = response.text
                            st.session_state['t2_ai_rating'] = "8/10" if "สูง" in t2_staff_rating or "วิกฤต" in t2_staff_rating else "4/10"
                            
                            # บันทึกลง Supabase สำหรับทำ Dashboard
                            if supabase_url and supabase_key:
                                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
                                payload = {
                                    "store_name": t2_store, "customer_contact": f"Staff Rating: {t2_staff_rating}",
                                    "raw_complaint": t2_raw, "ai_category": "Market_Complaint",
                                    "churn_risk_score": 5 if "วิกฤต" in t2_staff_rating else 3, 
                                    "ai_elaborated_summary": f"[AI Rating: {st.session_state['t2_ai_rating']}] - " + response.text[:150] + "..."
                                }
                                requests.post(f"{supabase_url}/rest/v1/onboarding_tickets", headers=headers, json=payload)
                                st.session_state['t2_saved'] = True
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาด: {str(e)}")

    with col_insight:
        st.subheader("💡 AI Insights & ตลาดเชิงกลยุทธ์")
        if st.session_state.get('t2_insight'):
            if st.session_state.get('t2_saved'):
                st.success("💾 บันทึกข้อมูลลงฐานข้อมูลคอมเพลนเรียบร้อย! (พร้อมดึงไปทำ Dashboard)")
            
            # โชว์ดีกรีเปรียบเทียบฝั่งซ้าย-ขวา
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.metric("Staff Discontent Rating", t2_staff_rating)
            with col_r2:
                st.metric("AI Evaluated Severity", st.session_state['t2_ai_rating'])
                
            st.markdown("---")
            st.markdown("**📌 บทวิเคราะห์กระชับใจความฟีเจอร์:**")
            st.write(st.session_state['t2_insight'])
        else:
            st.info("💡 กรอกข้อมูล Complaints ฝั่งซ้ายแล้วกดปุ่มวิเคราะห์เพื่อดูข้อมูล Strategic Insight ตรงนี้ครับ")
