import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt

# 1. ตั้งค่าพื้นฐาน
st.set_page_config(page_title="StoreHub CX Intelligence v4", layout="wide")
st.title("🚀 StoreHub CX Intelligence Portal")

# 2. Sidebar Configuration
st.sidebar.header("🔑 System Configuration")
supabase_url = st.sidebar.text_input("Supabase URL")
supabase_key = st.sidebar.text_input("Supabase Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# ฟังก์ชันดึงประวัติ (ใช้ทั้ง 2 แท็บ)
@st.cache_data(ttl=10)
def fetch_data(url, key, table="onboarding_tickets"):
    if url and key:
        try:
            headers = {"apikey": key.strip(), "Authorization": f"Bearer {key.strip()}"}
            res = requests.get(f"{url.strip()}/rest/v1/{table}?select=*&order=created_at.desc", headers=headers)
            if res.status_code == 200:
                return pd.DataFrame(res.json())
        except: pass
    return pd.DataFrame()

# ฟังก์ชันเรียก AI แบบ Auto-Detect รุ่น
def run_ai(api_key, content):
    try:
        genai.configure(api_key=api_key.strip())
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel_model = next((m for m in models if "flash" in m), models[0])
        model = genai.GenerativeModel(sel_model)
        return model.generate_content(content).text
    except Exception as e:
        return f"Error: {str(e)}"

tab1, tab2 = st.tabs(["📧 Ticket Escalation (Video Support)", "📊 Analysis Dashboard & Market Strategy"])

# --- TAB 1: Ticket Escalation ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("t1_form"):
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_detail = st.text_area("📝 รายละเอียดปัญหา (AI จะสรุปให้สั้นที่สุด)")
            # รองรับวิดีโอ
            t1_files = st.file_uploader("📸 แนบภาพหรือวิดีโอหลักฐาน", type=['png','jpg','jpeg','mp4','mov'], accept_multiple_files=True)
            submit1 = st.form_submit_button("✨ วิเคราะห์และร่างเมลสั้น", type="primary")

            if submit1 and gemini_key:
                with st.spinner("AI กำลังสรุปเคสแบบกระชับ..."):
                    prompt = f"สรุปปัญหานี้เป็นประโยคเดียวสั้นๆ ไม่เกิน 20 คำ เพื่อใส่ในอีเมล: {t1_detail}"
                    st.session_state['t1_res'] = run_ai(gemini_key, prompt)
                    # บันทึกลง Supabase (Optional)
    
    with c2:
        if 't1_res' in st.session_state:
            st.subheader("📩 ร่างอีเมล (ฉบับกระชับ)")
            mail_body = f"เรียน ทีม Care,\n\nพบปัญหา: {st.session_state['t1_res']}\n\nร้าน: {t1_store}\nรบกวนตรวจสอบและติดต่อกลับร้านค้าเพิ่มเติมครับ"
            st.text_area("เนื้อหา:", value=mail_body, height=150)
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(mail_body)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">📬 ส่ง Gmail</a>', unsafe_allow_html=True)

# --- TAB 2: Analysis & Dashboard ---
with tab2:
    # 1. Dashboard ส่วนบน
    st.subheader("📈 Dashboard Summary")
    df_all = fetch_data(supabase_url, supabase_key)
    if not df_all.empty:
        # จำลองหมวดหมู่สำหรับ Dashboard (ในงานจริงควรใช้ AI ช่วยจัดหมวดตอนบันทึก)
        df_all['category'] = df_all['ai_category'].fillna('Other')
        chart = alt.Chart(df_all).mark_bar().encode(
            x=alt.X('count()', title='จำนวนเคส'),
            y=alt.Y('category:N', sort='-x', title='หมวดหมู่'),
            color='category:N'
        ).properties(height=200)
        st.altair_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # 2. ส่วนกรอกข้อมูลและวิเคราะห์
    col_in, col_hist = st.columns([1, 1])
    with col_in:
        with st.form("t2_form"):
            t2_store = st.text_input("🏢 ชื่อร้าน (Market Analysis)")
            t2_raw = st.text_area("📝 รายละเอียดคอมเพลน / Feature Request")
            submit2 = st.form_submit_button("🧠 วิเคราะห์คู่แข่ง & บันทึก", type="primary")

            if submit2 and gemini_key:
                with st.spinner("AI กำลังเปรียบเทียบคู่แข่ง..."):
                    p2 = (f"วิเคราะห์สิ่งนี้: '{t2_raw}' โดยให้เปรียบเทียบชัดเจนว่าคู่แข่งไทยเช่น Wongnai POS, Ocha มีฟีเจอร์นี้หรือไม่ "
                          f"และรูปแบบของเขาเป็นอย่างไร ตอบแบบสั้น กระชับ เป็นข้อๆ")
                    st.session_state['t2_insight'] = run_ai(gemini_key, p2)
                    
                    # บันทึกลง Supabase
                    if supabase_url and supabase_key:
                        h = {"apikey": supabase_key.strip(), "Authorization": f"Bearer {supabase_key.strip()}", "Content-Type": "application/json"}
                        payload = {"store_name": t2_store, "raw_complaint": t2_raw, "ai_category": "Market_Analysis", "ai_elaborated_summary": st.session_state['t2_insight'][:200]}
                        requests.post(f"{supabase_url.strip()}/rest/v1/onboarding_tickets", headers=h, json=payload)
                        st.success("✅ บันทึกและวิเคราะห์สำเร็จ!")

    with col_hist:
        st.subheader("📜 History & Insights")
        if 't2_insight' in st.session_state:
            st.info(st.session_state['t2_insight'])
        
        st.write("ประวัติล่าสุด:")
        if not df_all.empty:
            st.dataframe(df_all[['created_at', 'store_name', 'ai_category', 'ai_elaborated_summary']].head(10), use_container_width=True)
            
            # ปุ่มส่งข้อมูลไป Google Sheet (จำลองการสร้าง CSV ให้โหลด หรือแจ้งเตือน)
            csv = df_all.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Download to Google Sheets (CSV)", data=csv, file_name='storehub_history.csv', mime='text/csv')
