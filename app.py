import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import requests
from PIL import Image
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="StoreHub CX Intelligence", layout="wide")

# ส่วนหัวโปรแกรม
st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 1. Sidebar สำหรับ Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase Project URL")
supabase_key = st.sidebar.text_input("Supabase API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# สร้าง Tabs
tab1, tab2 = st.tabs(["📧 Ticket & Email Escalation", "📊 Complaints Database & Insights"])

# --- TAB 1: Ticket & Email Escalation ---
with tab1:
    st.header("🎟️ เปิดทิคเก็ตใหม่ & ร่างอีเมลแจ้งทีม Care")
    
    col1, col2 = st.columns(2)
    with col1:
        store_name = st.text_input("🏢 ชื่อร้านค้า", placeholder="ระบุชื่อร้าน")
        customer_contact = st.text_input("👤 ผู้ติดต่อ / เบอร์โทร", placeholder="ชื่อลูกค้า หรือ เบอร์ติดต่อ")
        contact_time = st.text_input("⏰ เวลาที่สะดวกให้ติดต่อ", placeholder="เช่น ทันที หรือ หลัง 14:00 น.")
    with col2:
        raw_complaint = st.text_area("📝 รายละเอียดเคส", placeholder="กรอกปัญหาที่พบ...", height=120)
        uploaded_files = st.file_uploader("📸 แนบหลักฐาน (ภาพ)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

    if st.button("✨ ประมวลผลและร่างอีเมล", type="primary"):
        if not gemini_key:
            st.error("❌ กรุณากรอก Gemini API Key ที่ Sidebar")
        else:
            with st.spinner("AI กำลังสรุปข้อมูล..."):
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = f"""คุณคือผู้ช่วยทีม Support ของ StoreHub สรุปข้อมูลต่อไปนี้ให้สั้นและเป็นมืออาชีพที่สุด
                    ชื่อร้าน: {store_name}
                    ผู้ติดต่อ: {customer_contact}
                    เวลาสะดวก: {contact_time if contact_time else 'ติดต่อทันที'}
                    ปัญหา: {raw_complaint}
                    
                    ตอบเป็น JSON ภาษาไทย:
                    {{
                      "short_summary": "สรุปปัญหาแบบสั้นกระชับ 1 ประโยค",
                      "email_body": "ร่างเนื้อหาอีเมลโดยระบุรายละเอียดตามที่ได้รับมาให้ครบถ้วน"
                    }}"""
                    
                    response = model.generate_content(prompt)
                    ai_res = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    
                    # แสดงผล Panel สำหรับส่งเมล
                    st.success("✅ สรุปข้อมูลเรียบร้อย!")
                    st.subheader("📧 ตรวจสอบอีเมลก่อนส่งไปที่ care.th@storehub.com")
                    
                    # หัวข้อเมลอัตโนมัติ
                    email_subject = f"Escalation: {store_name} | {ai_res['short_summary']}"
                    st.text_input("หัวข้ออีเมล:", value=email_subject)
                    
                    # เนื้อหาเมล
                    footer = "\n\nรบกวนติดต่อกลับร้านค้าและสอบถามรายละเอียดเพิ่มเติม"
                    final_body = f"เรียน ทีม Care,\n\n{ai_res['email_body']}\n\n" + \
                                 f"🏢 ชื่อร้าน: {store_name}\n" + \
                                 f"👤 ผู้ติดต่อ: {customer_contact}\n" + \
                                 f"⏰ เวลาที่สะดวก: {contact_time if contact_time else 'ติดต่อทันที'}" + \
                                 footer
                    
                    edited_body = st.text_area("เนื้อหาอีเมล:", value=final_body, height=250)
                    
                    # ปุ่ม Link ไป Gmail
                    encoded_subject = urllib.parse.quote(email_subject)
                    encoded_body = urllib.parse.quote(edited_body)
                    gmail_link = f"https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_subject}&body={encoded_body}"
                    
                    st.markdown(f'<a href="{gmail_link}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📩 กดเพื่อเปิด Gmail และส่งทันที</a>', unsafe_allow_html=True)
                    st.info("💡 อย่าลืมลากไฟล์ภาพแนบในหน้า Gmail อีกครั้งเพื่อความชัวร์")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --- TAB 2: Complaints Database ---
with tab2:
    st.header("📊 Complaints Database & Analytics")
    st.markdown("ส่วนนี้ใช้สำหรับบันทึกข้อมูลเพื่อนำไปทำ Dashboard หาโอกาสพัฒนา (Insights)")

    if st.button("🔄 ดึงข้อมูลประวัติล่าสุด"):
        if not (supabase_url and supabase_key):
            st.warning("⚠️ กรุณากรอก Supabase URL และ Key ที่ Sidebar เพื่อดูข้อมูล")
        else:
            try:
                headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
                res = requests.get(f"{supabase_url}/rest/v1/onboarding_tickets?select=*&order=created_at.desc", headers=headers)
                if res.status_code == 200:
                    df = pd.DataFrame(res.json())
                    if not df.empty:
                        # แต่งตารางให้สวย
                        st.dataframe(df[['created_at', 'store_name', 'ai_category', 'churn_risk_score', 'ai_elaborated_summary']], use_container_width=True)
                        
                        # ส่วน Insights เบื้องต้น
                        col_stat1, col_stat2 = st.columns(2)
                        with col_stat1:
                            st.subheader("📈 ปัญหาแบ่งตามหมวดหมู่")
                            st.bar_chart(df['ai_category'].value_counts())
                        with col_stat2:
                            st.subheader("⚠️ ระดับความเสี่ยงเฉลี่ย")
                            st.metric("Avg. Churn Risk", round(df['churn_risk_score'].mean(), 2))
                    else:
                        st.info("ยังไม่มีข้อมูลในระบบ")
            except Exception as e:
                st.error(f"ไม่สามารถดึงข้อมูลได้: {str(e)}")

    st.markdown("---")
    st.caption("StoreHub CX Intelligence Tool v3.0 | พัฒนาเพื่อทีม Onboarding โดยเฉพาะ")
