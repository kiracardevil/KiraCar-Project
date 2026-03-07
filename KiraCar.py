import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# --- 1. การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="KiraCar Pro Plus", layout="wide", page_icon="🏎️")

# --- 2. จุดเชื่อมต่อข้อมูล (ตรวจสอบลิงก์ให้ถูกต้อง) ---
# ต้องลงท้ายด้วย /formResponse เท่านั้น
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"

# ลิงก์ CSV จากการ Publish to web
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRTaXnMfRxy-JdgCp4rCqJzdUES16l77D8_Okbf-bQnjxnu5HeRyS5agIokGCfG_3x3oCK7VCdlGXG2/pub?gid=754879556&single=true&output=csv"

# --- 3. ฟังก์ชันหลักสำหรับบันทึกข้อมูล (ไม่ต้องแก้แล้ว) ---
def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
    payload = {
        "entry.1392091793": model,
        "entry.1772417832": buy_price,
        "entry.499287053": repair_cost,
        "entry.50844596": status,
        "entry.1300688537": sell_price,
    }
    try:
        # ส่งข้อมูลแบบเงียบๆ ไม่ต้อง Login Google
        res = requests.post(FORM_URL, data=payload)
        return res.status_code == 200 or res.status_code == 302
    except:
        return False

# --- 4. โหลดข้อมูลมาแสดงผล ---
def load_data():
    try:
        # ใส่ตัวแปรสุ่มเพื่อป้องกัน Cache ข้อมูลเก่า
        import time
        df_raw = pd.read_csv(f"{SHEET_CSV_URL}&t={int(time.time())}")
        # ตั้งชื่อหัวข้อให้ตรงกับ Sheets
        df_raw.columns = ['ประทับเวลา', 'รุ่นรถ', 'ราคาทุน', 'ค่าซ่อม', 'สถานะ', 'ราคาขาย']
        df_raw['ราคาทุน'] = pd.to_numeric(df_raw['ราคาทุน'], errors='coerce').fillna(0)
        df_raw['ค่าซ่อม'] = pd.to_numeric(df_raw['ค่าซ่อม'], errors='coerce').fillna(0)
        df_raw['ราคาขาย'] = pd.to_numeric(df_raw['ราคาขาย'], errors='coerce').fillna(0)
        df_raw['กำไร'] = df_raw['ราคาขาย'] - (df_raw['ราคาทุน'] + df_raw['ค่าซ่อม'])
        return df_raw
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- 5. หน้าตาโปรแกรม (UI) ---
st.title("🏎️ KiraCar Pro: Smart Inventory Management")

menu = st.sidebar.radio("เมนูหลัก", ["📊 Dashboard", "➕ บันทึกรถเข้าใหม่", "🔎 ค้นหาข้อมูล"])

if menu == "📊 Dashboard":
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 รถทั้งหมด", f"{len(df)} คัน")
        c2.metric("💰 ทุนจมรวม", f"{ (df['ราคาทุน'].sum() + df['ค่าซ่อม'].sum()):,.0f} ฿")
        c3.metric("📈 กำไรสะสม", f"{df['กำไร'].sum():,.0f} ฿")
        
        st.subheader("📋 รายการล่าสุด")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("ยังไม่มีข้อมูล หรือระบบกำลังโหลดไฟล์ CSV กรุณารอสักครู่...")

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("📋 ลงทะเบียนรถคันใหม่")
    # สำคัญ: ต้องใส่ตัวแปรไว้ในฟอร์มเพื่อให้ทำงานได้ถูกต้อง
    with st.form("add_car_form", clear_on_submit=True):
        f_model = st.text_input("ชื่อรุ่นรถ/ปี")
        col_price, col_repair = st.columns(2)
        with col_price:
            f_buy = st.number_input("ราคาทุนซื้อ", min_value=0, step=1000)
        with col_repair:
            f_repair = st.number_input("ค่าซ่อม", min_value=0, step=500)
        
        col_status, col_sell = st.columns(2)
        with col_status:
            f_status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "จองแล้ว", "ขายแล้ว"])
        with col_sell:
            f_sell = st.number_input("ราคาขาย", min_value=0, step=1000)
        
        submit = st.form_submit_button("🚀 บันทึกข้อมูล")
        
        if submit:
            if f_model:
                with st.spinner('กำลังบันทึก...'):
                    # เรียกใช้ฟังก์ชันบันทึก
                    success = save_to_google_form(f_model, f_buy, f_repair, f_status, f_sell)
                    if success:
                        st.success(f"บันทึกข้อมูล {f_model} เรียบร้อย!")
                        st.info("รอข้อมูลอัปเดตจาก Google Sheets ประมาณ 1 นาที")
                        st.balloons()
                    else:
                        st.error("บันทึกไม่สำเร็จ ตรวจสอบการตั้งค่า FORM_URL")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")

elif menu == "🔎 ค้นหาข้อมูล":
    search = st.text_input("พิมพ์ชื่อรุ่นที่ต้องการค้นหา")
    if not df.empty:
        search_df = df[df['รุ่นรถ'].str.contains(search, case=False, na=False)]
        st.dataframe(search_df, use_container_width=True)

st.sidebar.write("---")
if st.sidebar.button("🔄 รีเฟรชข้อมูล"):
    st.rerun()
