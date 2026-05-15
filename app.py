import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
from PIL import Image
import urllib.parse
import altair as alt

# 1. Page Configuration
st.set_page_config(page_title="StoreHub CX Intelligence Portal", layout="wide")
st.title("🚀 StoreHub CX Intelligence Portal")
st.markdown("---")

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

# ฟังก์ชันเรียก AI แบบเน้นการวิเคราะห์ภาพละเอียดและประหยัดโควตา
def run_ai(api_key, content_list):
    try:
        genai.configure(api_key=api_key.strip())
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected = next((m for m in available_models if "flash" in m), available_models[0])
        model = genai.GenerativeModel(selected)
        response = model.generate_content(content_list)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ โควตาเต็ม กรุณารอ 1 นาทีแล้วลองใหม่"
        return f"AI Error: {str(e)}"

tab1, tab2 = st.tabs(["📧 Ticket Escalation (Detailed)", "📊 Market Analysis & Dashboard"])

# --- TAB 1: Ticket Escalation ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("t1_form"):
            st.subheader("📥 บันทึกและวิเคราะห์เคสละเอียด")
            t1_store = st.text_input("🏢 ชื่อร้านค้า")
            t1_contact = st.text_input("👤 ข้อมูลผู้ติดต่อ (ชื่อ/เบอร์)")
            t1_time = st.text_input("⏰ เวลาสะดวกให้ติดต่อกลับ")
            t1_raw = st.text_area("📝 รายละเอียดเพิ่มเติม")
            t1_files = st.file_uploader("📸 แนบภาพหลักฐาน (AI จะวิเคราะห์จากภาพนี้)", type=['png','jpg','jpeg'])
            
            if st.form_submit_button("✨ วิเคราะห์ภาพและร่างเมล", type="primary"):
                if gemini_key and t1_files:
                    with st.spinner("AI กำลังวิเคราะห์รายละเอียดจากภาพ..."):
                        img = Image.open(t1_files)
                        # Prompt สั่งให้วิเคราะห์ละเอียดแต่สรุปเป็นข้อสั้นๆ
                        prompt = (
                            "จากภาพที่แนบมา ช่วยวิเคราะห์ปัญหาหรือคอมเพลนที่เกิดขึ้น "
                            "โดยระบุเป็นข้อๆ สั้นๆ กระชับ (Bullet points) "
                            "และสรุปใจความสำคัญที่ต้องแก้ไขด่วน"
                        )
                        st.session_state['t1_analysis'] = run_ai(gemini_key, [prompt, img])
                elif not t1_files:
                    st.warning("กรุณาแนบภาพเพื่อให้ AI วิเคราะห์รายละเอียดครับ")

    with c2:
        if 't1_analysis' in st.session_state:
            st.subheader("📧 ร่างอีเมล (ลำดับตามระเบียบ)")
            
            # จัดลำดับเนื้อหาอีเมลตามที่คุณต้องการ
            analysis_text = st.session_state['t1_analysis']
            mail_content = (
                f"เรียน ทีม Care,\n\n"
                f"**ข้อมูลผู้ติดต่อ:** {t1_contact}\n"
                f"**เวลาติดต่อกลับ:** {t1_time if t1_time else 'ทันที'}\n\n"
                f"**รายละเอียดวิเคราะห์จากภาพและคำบัญชีย้าย:**\n{analysis_text}\n\n"
                f"รบกวนทีมแคร์ติดต่อกลับและสอบถามรายละเอียดเพิ่มเติม"
            )
            
            edited_mail = st.text_area("ตรวจสอบเนื้อหา:", value=mail_content, height=350)
            
            encoded_su = urllib.parse.quote(f"Escalation: {t1_store}")
            encoded_bo = urllib.parse.quote(edited_mail)
            st.markdown(f'<a href="https://mail.google.com/mail/?view=cm&fs=1&to=care.th@storehub.com&su={encoded_su}&body={encoded_bo}" target="_blank" style="background-color: #D44638; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📬 เปิด Gmail เพื่อส่งทันที</a>', unsafe_allow_html=True)

# --- TAB 2: Dashboard (คงเดิมและเสถียร) ---
with tab2:
    df_history = fetch_data(supabase_url, supabase_key)
    st.subheader("📈 Dashboard & History")
    if not df_history.empty:
        chart = alt.Chart(df_history).mark_bar().encode(x='count()', y=alt.Y('ai_category:N', sort='-x'), color='ai_category:N').properties(height=200)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df_history[['created_at', 'store_name', 'ai_elaborated_summary']].head(10), use_container_width=True)
