import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt

# 1. ตั้งค่าหน้าเว็บพื้นฐาน
st.set_page_config(page_title="StoreHub CX Intelligence Portal", layout="wide")
st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase URL")
supabase_key = st.sidebar.text_input("Supabase Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงข้อมูลประวัติ
@st.cache_data(ttl=5)
def fetch_data(url, key):
    if url and key:
        try:
            headers = {"apikey": key.strip(), "Authorization": f"Bearer {key.strip()}"}
            res = requests.get(f"{url.strip()}/rest/v1/onboarding_tickets?select=*&order=created_at.desc", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except: pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI แบบค้นหาโมเดลที่ใช้งานได้จริงอัตโนมัติ (แก้ปัญหา 404 ถาวร)
def run_ai(api_key, content_list):
    try:
        genai.configure(api_key=api_key.strip())
        # ค้นหาโมเดลทั้งหมดที่บัญชีนี้เข้าถึงได้
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # ลำดับความสำคัญ: ลองหา 1.5-flash -> 1.5-pro -> 1.0-pro -> ตัวแรกที่เจอ
        selected = next((m for m in available_models if "1.5-flash" in m), 
                   next((m for m in available_models if "1.5-pro" in m), 
                   next((m for m in available_models if "pro" in m), available_models[0])))
        
        model = genai.GenerativeModel(selected)
        response = model.generate_content(content_list)
        return response.text
    except Exception as e:
        return f"AI Connection Error: {str(e)}"

tab1, tab2 = st.tabs(["📧 Ticket Escalation (Video Support)", "📊 Market Analysis & Dashboard"])

# --- TAB 1: Ticket Escalation ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("t1_form"):
            st.subheader("📥 บันทึกเคสใหม่")
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_contact = st.text_input("👤 ผู้ติดต่อ")
            t1_raw = st.text_area("📝 รายละเอียดปัญหา")
            t1_files = st.file_uploader("📸 แนบภาพหรือวิดีโอ", type=['png','jpg','jpeg','mp4','mov'], accept_multiple_files=True)
            submit1 = st.form_submit_button("✨ สรุปและร่างเมลสั้น", type="primary")

            if submit1 and gemini_key:
                with st.spinner("AI กำลังสรุปข้อมูล..."):
                    prompt = f"สรุปปัญหานี้เป็นประโยคเดียวสั้นๆ กระชับที่สุด ไม่เกิน 15 คำ: {t1_raw}"
                    st.session_state['t1_res'] = run_ai(gemini_key, [prompt])
    
    with c2:
        if 't1_res' in st.session_state:
            st.subheader("📧 ร่างอีเมลแจ้งทีม Care")
            mail_body = f"เรียน ทีม Care,\n\nพบปัญหา: {st.session_state['t1_res']}\n\n🏢 ร้าน: {t1_store}\nรบกวนตรวจสอบและติดต่อกลับร้านค้าเพิ่มเติมครับ"
            st.text_area("เนื้อหาอีเมล:", value=mail_body, height=180)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📬 เปิด Gmail ส่งหลักฐาน</a>', unsafe_allow_html=True)

# --- TAB 2: Analysis & Dashboard ---
with tab2:
    df_history = fetch_data(supabase_url, supabase_key)
    st.subheader("📊 Dashboard: Top Issues Summary")
    if not df_history.empty:
        chart_data = df_history['ai_category'].fillna('General').value_counts().reset_index()
        chart_data.columns = ['Category', 'Count']
        st.altair_chart(alt.Chart(chart_data).mark_bar().encode(x='Count:Q', y=alt.Y('Category:N', sort='-x'), color='Category:N').properties(height=200), use_container_width=True)
    
    st.markdown("---")
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("t2_form"):
            st.subheader("🕵️ Market Strategic Analysis")
            t2_store = st.text_input("🏢 ชื่อร้าน")
            t2_staff_rating = st.select_slider("🚩 Staff Rating", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียด (Complaint / Request)")
            t2_img = st.file_uploader("🖼️ อัปโหลดภาพหลักฐาน", type=['png', 'jpg', 'jpeg'])
            if st.form_submit_button("🧠 วิเคราะห์และบันทึก", type="primary"):
                if gemini_key:
                    with st.spinner("AI กำลังวิเคราะห์..."):
                        p2 = f"วิเคราะห์สิ่งนี้เทียบกับคู่แข่งไทย (Wongnai, Ocha, FoodStory): '{t2_raw}' สรุปสั้น กระชับ เป็นข้อๆ และประเมินว่าเป็น Must-have หรือไม่"
                        content = [p2]
                        if t2_img: content.append(Image.open(t2_img))
                        st.session_state['t2_insight'] = run_ai(gemini_key, content)
                        if supabase_url and supabase_key:
                            h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                            requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json={"store_name": t2_store, "raw_complaint": t2_raw, "ai_category": "Market_Analysis", "ai_elaborated_summary": st.session_state['t2_insight'][:300]})
                            st.success("✅ บันทึกสำเร็จ!")

    with col_hist:
        st.subheader("📜 History & Insights")
        if 't2_insight' in st.session_state: st.info(st.session_state['t2_insight'])
        if not df_history.empty:
            st.dataframe(df_history[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']].head(10), use_container_width=True)
            st.download_button("📥 Download CSV for Google Sheets", data=df_history.to_csv(index=False).encode('utf-8'), file_name='storehub_insights.csv', mime='text/csv')
