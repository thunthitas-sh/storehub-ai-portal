import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt

# 1. ตั้งค่าพื้นฐาน
st.set_page_config(page_title="StoreHub CX Intelligence Portal", layout="wide")
st.title("🚀 StoreHub CX Intelligence Portal")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase URL")
supabase_key = st.sidebar.text_input("Supabase Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงประวัติ
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

# ฟังก์ชันเรียก AI แบบรองรับ Multi-modal (Text + Image)
def run_ai(api_key, content_list):
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(content_list)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

tab1, tab2 = st.tabs(["📧 Escalation (Video Support)", "📊 Market Analysis & Dashboard"])

# --- TAB 1: Ticket Escalation ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("t1_form"):
            st.subheader("📥 บันทึกเคสใหม่")
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_detail = st.text_area("📝 รายละเอียดปัญหา")
            t1_files = st.file_uploader("📸 แนบภาพหรือวิดีโอ", type=['png','jpg','jpeg','mp4','mov'], accept_multiple_files=True)
            submit1 = st.form_submit_button("✨ สรุปและร่างเมล", type="primary")

            if submit1 and gemini_key:
                with st.spinner("AI กำลังทำงาน..."):
                    prompt = f"สรุปปัญหานี้เป็นประโยคเดียวสั้นๆ กระชับที่สุด: {t1_detail}"
                    st.session_state['t1_res'] = run_ai(gemini_key, [prompt])
    
    with c2:
        if 't1_res' in st.session_state:
            st.subheader("📧 ร่างอีเมล")
            mail_body = f"เรียน ทีม Care,\n\nพบปัญหา: {st.session_state['t1_res']}\n\nร้าน: {t1_store}\nรบกวนตรวจสอบเพิ่มเติมครับ"
            st.text_area("เนื้อหา:", value=mail_body, height=150)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📩 ส่ง Gmail</a>', unsafe_allow_html=True)

# --- TAB 2: Analysis & Dashboard ---
with tab2:
    df_history = fetch_data(supabase_url, supabase_key)
    
    # 1. แดชบอร์ดสรุปเบื้องต้น
    st.subheader("📈 Dashboard: Top Issues & Requests")
    if not df_history.empty:
        # สรุปหมวดหมู่เคส
        chart_data = df_history['ai_category'].value_counts().reset_index()
        chart_data.columns = ['Category', 'Count']
        bar_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Count:Q', title='จำนวนเคส'),
            y=alt.Y('Category:N', sort='-x', title='หมวดหมู่'),
            color='Category:N'
        ).properties(height=250)
        st.altair_chart(bar_chart, use_container_width=True)
    
    st.markdown("---")

    # 2. ส่วนวิเคราะห์คู่แข่ง
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("t2_form"):
            st.subheader("🕵️ Market Analysis & Deep Insights")
            t2_store = st.text_input("🏢 ชื่อร้านค้า")
            t2_staff_rating = st.select_slider("🚩 เรทความไม่พอใจลูกค้า (Staff Rating)", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียดคอมเพลน / Feature Request")
            t2_img = st.file_uploader("🖼️ อัปโหลดภาพหลักฐานเพื่อวิเคราะห์", type=['png', 'jpg', 'jpeg'])
            submit2 = st.form_submit_button("🧠 วิเคราะห์กลยุทธ์ตลาด & บันทึก", type="primary")

            if submit2 and gemini_key:
                with st.spinner("AI กำลังเปรียบเทียบตลาด..."):
                    analysis_prompt = (
                        f"วิเคราะห์สิ่งนี้: '{t2_raw}' โดยเปรียบเทียบชัดเจนว่าคู่แข่งไทยอย่าง Wongnai POS, Ocha มีฟีเจอร์นี้หรือไม่ "
                        "และรูปแบบเขาเป็นอย่างไร สรุปสั้น กระชับ เป็นข้อๆ และประเมินว่าเป็น Must-have หรือไม่"
                    )
                    content = [analysis_prompt]
                    if t2_img: content.append(Image.open(t2_img))
                    
                    st.session_state['t2_insight'] = run_ai(gemini_key, content)
                    
                    # บันทึกลง Supabase
                    if supabase_url and supabase_key:
                        h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                        payload = {
                            "store_name": t2_store, 
                            "raw_complaint": t2_raw, 
                            "ai_category": "Feature_Request" if "ฟีเจอร์" in t2_raw else "Market_Complaint",
                            "churn_risk_score": 5 if t2_staff_rating == "วิกฤต" else 3,
                            "ai_elaborated_summary": st.session_state['t2_insight'][:200]
                        }
                        requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json=payload)
                        st.success("✅ บันทึกและวิเคราะห์เรียบร้อย!")

    with col_hist:
        st.subheader("📜 ประวัติล่าสุด")
        if 't2_insight' in st.session_state:
            st.info(st.session_state['t2_insight'])
        
        if not df_history.empty:
            st.dataframe(df_history[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']].head(10), use_container_width=True)
            # ปุ่มส่งออก Google Sheets (CSV)
            csv = df_history.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Export to Google Sheets (CSV)", data=csv, file_name='storehub_market_insights.csv', mime='text/csv')
        else:
            st.write("ยังไม่มีข้อมูลประวัติในระบบ")
