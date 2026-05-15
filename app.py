import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt
import io

# 1. ตั้งค่าพื้นฐาน (ต้องเป็นคำสั่งแรก)
st.set_page_config(page_title="StoreHub CX Intelligence Portal", layout="wide")

st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase URL")
supabase_key = st.sidebar.text_input("Supabase Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงข้อมูลจาก Supabase
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

# ฟังก์ชันเรียก AI แบบระบุรุ่นตรงเพื่อแก้ปัญหา 404
def run_ai(api_key, content_list):
    try:
        genai.configure(api_key=api_key.strip())
        # ระบุรุ่นมาตรฐานที่รองรับ Multi-modal (ภาพ/วิดีโอ)
        model = genai.GenerativeModel('gemini-1.5-flash')
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
            t1_detail = st.text_area("📝 รายละเอียดปัญหา")
            t1_files = st.file_uploader("📸 แนบภาพหรือวิดีโอ", type=['png','jpg','jpeg','mp4','mov'], accept_multiple_files=True)
            submit1 = st.form_submit_button("✨ สรุปและร่างเมล", type="primary")

            if submit1 and gemini_key:
                with st.spinner("AI กำลังสรุปข้อมูล..."):
                    prompt = f"สรุปปัญหานี้เป็นประโยคเดียวสั้นๆ กระชับที่สุด ไม่เกิน 15 คำ: {t1_detail}"
                    st.session_state['t1_res'] = run_ai(gemini_key, [prompt])
    
    with c2:
        if 't1_res' in st.session_state:
            st.subheader("📧 ร่างอีเมลแจ้งทีม Care")
            mail_body = f"เรียน ทีม Care,\n\nสรุปปัญหา: {st.session_state['t1_res']}\n\n🏢 ร้าน: {t1_store}\nรบกวนตรวจสอบและติดต่อกลับร้านค้าเพิ่มเติมครับ"
            st.text_area("เนื้อหาอีเมล:", value=mail_body, height=180)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📬 เปิด Gmail เพื่อส่งหลักฐาน</a>', unsafe_allow_html=True)
            st.info("💡 ไฟล์วิดีโอ/ภาพจะไม่ได้แนบไปอัตโนมัติ รบกวนลากไฟล์ใส่ในหน้า Gmail อีกครั้งครับ")

# --- TAB 2: Analysis & Dashboard ---
with tab2:
    df_history = fetch_data(supabase_url, supabase_key)
    
    # 1. แดชบอร์ดสรุป (Visual Insights)
    st.subheader("📊 Dashboard: Top Issues Summary")
    if not df_history.empty:
        # วิเคราะห์หมวดหมู่
        df_history['category'] = df_history['ai_category'].fillna('Market_Complaint')
        chart_data = df_history['category'].value_counts().reset_index()
        chart_data.columns = ['Category', 'Count']
        
        bar_chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Count:Q', title='จำนวนเคส'),
            y=alt.Y('Category:N', sort='-x', title='ประเภทข้อมูล'),
            color='Category:N'
        ).properties(height=200)
        st.altair_chart(bar_chart, use_container_width=True)
    
    st.markdown("---")

    # 2. ส่วนวิเคราะห์คู่แข่ง
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.container(border=True):
            st.subheader("🕵️ Market Strategic Analysis")
            t2_store = st.text_input("🏢 ชื่อบัญชีร้านค้า", key="t2_store_input")
            t2_staff_rating = st.select_slider("🚩 Staff Rating (ระดับความไม่พอใจ)", options=["ต่ำ", "กลาง", "สูง", "วิกฤต"])
            t2_raw = st.text_area("📝 รายละเอียด (Complaint / Feature Request)")
            t2_img = st.file_uploader("🖼️ อัปโหลดภาพเพื่อวิเคราะห์เชิงลึก", type=['png', 'jpg', 'jpeg'])
            
            if st.button("🧠 วิเคราะห์กลยุทธ์ & บันทึกข้อมูล", type="primary"):
                if gemini_key:
                    with st.spinner("AI กำลังวิเคราะห์ข้อมูลคู่แข่ง..."):
                        analysis_prompt = (
                            f"วิเคราะห์ข้อมูลนี้: '{t2_raw}' "
                            "โดยระบุชื่อคู่แข่ง POS ในไทยที่ชัดเจน (เช่น Wongnai POS, Ocha, FoodStory) "
                            "ว่าเขามีฟีเจอร์นี้หรือไม่ รูปแบบเป็นอย่างไร สรุปสั้น กระชับ เป็นข้อๆ "
                            "และประเมินว่าเป็น Must-have สำหรับเราหรือไม่"
                        )
                        content = [analysis_prompt]
                        if t2_img:
                            content.append(Image.open(t2_img))
                        
                        st.session_state['t2_insight'] = run_ai(gemini_key, content)
                        
                        # บันทึกลง Supabase
                        if supabase_url and supabase_key:
                            h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                            payload = {
                                "store_name": t2_store, 
                                "raw_complaint": t2_raw, 
                                "ai_category": "Feature_Request" if "ฟีเจอร์" in t2_raw or "อยากให้" in t2_raw else "Market_Complaint",
                                "churn_risk_score": 5 if t2_staff_rating == "วิกฤต" else (3 if t2_staff_rating == "กลาง" else 1),
                                "ai_elaborated_summary": st.session_state['t2_insight'][:300]
                            }
                            requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json=payload)
                            st.success("✅ วิเคราะห์และบันทึกสำเร็จ!")
                            st.rerun()

    with col_hist:
        st.subheader("📜 ประวัติล่าสุด & Insights")
        if 't2_insight' in st.session_state:
            st.info(f"**AI Analysis:**\n\n{st.session_state['t2_insight']}")
        
        if not df_history.empty:
            st.write("ตารางประวัติข้อมูลล่าสุด:")
            st.dataframe(df_history[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']].head(10), use_container_width=True)
            
            # ปุ่ม Export ไป Google Sheets (ผ่าน CSV)
            csv = df_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV for Google Sheets",
                data=csv,
                file_name='storehub_market_insights.csv',
                mime='text/csv',
            )
        else:
            st.write("ยังไม่มีข้อมูลในฐานข้อมูล")
