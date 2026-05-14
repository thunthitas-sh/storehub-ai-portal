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

# ฟังก์ชันดึงข้อมูลจาก Supabase
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

# ฟังก์ชันกลางสำหรับเรียกใช้ AI พร้อมระบบ Fallback ป้องกัน Error 404
def call_gemini_ai(prompt_content):
    gkey = gemini_key.strip()
    genai.configure(api_key=gkey)
    # ลำดับโมเดลที่ต้องการใช้ (ถ้าตัวแรก
