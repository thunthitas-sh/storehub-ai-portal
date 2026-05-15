import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt

# 1. ตั้งค่าหน้าเว็บให้เสถียรที่สุด
st.set_page_config(page_title="StoreHub Intelligence Portal", layout="wide")
st.title("🚀 StoreHub CX Intelligence Portal")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase URL")
supabase_key = st.sidebar.text_input("Supabase Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงประวัติ (ย้ายมาไว้ข้างนอกเพื่อให้ดึงข้อมูลใหม่ทุกครั้งที่สลับแท็บ)
def fetch_data(table="onboarding_tickets"):
    if supabase_url and supabase_key:
        try:
            headers = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}"}
            res = requests.get(f"{supabase_url.strip()}/rest/v1/{table}?select=*&order=created_at.desc", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except: pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI
def run_ai(content_list):
    try:
        genai.configure(api_key=gemini_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(content_list)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# สร้างแท็บ
tab1, tab2 = st.tabs(["📧 Ticket Escalation (Detailed)", "🛡️ Market Analysis & Dashboard"])

# --- TAB 1: Ticket Escalation ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("t1_form"):
            st.subheader("📥 บันทึกและวิเคราะห์เคสละเอียด")
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_contact = st.text_input("👤 ข้อมูลผู้ติดต่อ (ชื่อ/เบอร์)")
            t1_time = st.text_input("⏰ เวลาสะดวกให้ติดต่อกลับ")
            t1_files = st.file_uploader("📸 แนบภาพหรือวิดีโอ (AI วิเคราะห์จากไฟล์นี้)", type=['png','jpg','jpeg','mp4','mov'])
            submit1 = st.form_submit_button("✨ วิเคราะห์และร่างเมลละเอียด", type="primary")

            if submit1 and gemini_key:
                with st.spinner("AI กำลังวิเคราะห์..."):
                    # เตรียมข้อมูลส่งให้ AI
                    content = ["จากภาพ/ไฟล์ที่แนบ ช่วยวิเคราะห์ปัญหาหรือคอมเพลนที่เกิดขึ้น ระบุเป็นข้อๆ สั้นๆ กระชับที่สุด"]
                    if t1_files:
                        if t1_files.type.startswith('image'):
                            content.append(Image.open(t1_files))
                        # สำหรับวิดีโอ AI Flash ปัจจุบันจะอ่าน Metadata หรือภาพนิ่ง (ถ้าต้องการส่งไฟล์วิดีโอจริงต้องใช้พาร์ท Upload API)
                    
                    st.session_state['t1_analysis'] = run_ai(content)

    with c2:
        if 't1_analysis' in st.session_state:
            st.subheader("📧 ร่างอีเมลแจ้งทีม Care")
            mail_body = (
                f"เรียน ทีม Care,\n\n"
                f"ข้อมูลผู้ติดต่อ: {t1_contact}\n"
                f"เวลาติดต่อกลับ: {t1_time if t1_time else 'ทันที'}\n\n"
                f"รายละเอียดวิเคราะห์จากภาพและคำบัญชีย้าย:\n{st.session_state['t1_analysis']}\n\n"
                f"รบกวนทีมแคร์ติดต่อกลับและสอบถามรายละเอียดเพิ่มเติม"
            )
            st.text_area("ตรวจสอบเนื้อหา:", value=mail_body, height=300)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📬 ส่ง Gmail</a>', unsafe_allow_html=True)

# --- TAB 2: Analysis & Dashboard ---
with tab2:
    # ดึงข้อมูลใหม่ทุกครั้งที่เปิดแท็บนี้
    df_history = fetch_data()
    
    st.subheader("📈 Dashboard: Case Categories")
    if not df_history.empty:
        chart_data = df_history['ai_category'].fillna('General').value_counts().reset_index()
        chart_data.columns = ['Category', 'Count']
        st.altair_chart(alt.Chart(chart_data).mark_bar().encode(x='Count:Q', y=alt.Y('Category:N', sort='-x'), color='Category:N').properties(height=200), use_container_width=True)
    
    st.markdown("---")
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("t2_form"):
            st.subheader("🕵️ Market Strategic Analysis")
            t2_store = st.text_input("🏢 ชื่อบัญชีร้านค้า")
            t2_rating = st.select_slider("🚩 Staff Rating", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_detail = st.text_area("📝 รายละเอียดคอมเพลน")
            t2_img = st.file_uploader("🖼️ ภาพหลักฐาน", type=['png', 'jpg', 'jpeg'])
            submit2 = st.form_submit_button("🧠 วิเคราะห์กลยุทธ์ & บันทึก", type="primary")

            if submit2 and gemini_key:
                with st.spinner("AI กำลังเปรียบเทียบตลาด..."):
                    prompt = f"วิเคราะห์สิ่งนี้: '{t2_detail}' เทียบกับคู่แข่ง POS ไทย (Wongnai, Ocha) เขามีฟีเจอร์นี้ไหม รูปแบบเป็นอย่างไร สรุปสั้นๆ และประเมินว่าเป็น Must-have หรือไม่"
                    content2 = [prompt]
                    if t2_img: content2.append(Image.open(t2_img))
                    
                    insight = run_ai(content2)
                    st.session_state['t2_insight'] = insight
                    
                    # บันทึกลง Supabase
                    if supabase_url and supabase_key:
                        h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                        requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json={
                            "store_name": t2_store, "raw_complaint": t2_detail, 
                            "ai_category": "Market_Analysis", "ai_elaborated_summary": insight[:300]
                        })
                        st.success("💾 บันทึกสำเร็จ!")

    with col_hist:
        st.subheader("📜 History & Insights")
        if 't2_insight' in st.session_state:
            st.info(st.session_state['t2_insight'])
        if not df_history.empty:
            st.dataframe(df_history[['created_at', 'store_name', 'ai_elaborated_summary']].head(10), use_container_width=True)
            st.download_button("📥 Download CSV for Sheets", data=df_history.to_csv(index=False).encode('utf-8'), file_name='storehub_insights.csv', mime='text/csv')
        else:
            st.write("ยังไม่มีข้อมูลประวัติในระบบ")
