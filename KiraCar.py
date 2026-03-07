import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 1. ตั้งค่าการเชื่อมต่อ (เช็คให้ชัวร์ว่าไม่มีช่องว่างปิดท้าย) ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRTaXnMfRxy-JdgCp4rCqJzdUES16l77D8_Okbf-bQnjxnu5HeRyS5agIokGCfG_3x3oCK7VCdlGXG2/pub?gid=754879556&single=true&output=csv"

# --- 2. ฟังก์ชันบันทึกข้อมูล (ปรับปรุงใหม่เพื่อเช็ค Error) ---
def save_to_google_form(model, buy, repair, status, sell):
    # ใช้รหัส entry เดิมที่คุณเคยส่งมา
    payload = {
        "entry.1392091793": model,
        "entry.1772417832": buy,
        "entry.499287053": repair,
        "entry.50844596": status,
        "entry.1300688537": sell
    }
    try:
        response = requests.post(FORM_URL, data=payload, timeout=10)
        # ถ้าสำเร็จ Google จะตอบกลับมาด้วย Status 200 หรือ 302
        if response.status_code in [200, 302]:
            return True, "สำเร็จ"
        else:
            return False, f"Google ตอบกลับด้วยรหัส: {response.status_code}"
    except Exception as e:
        return False, str(e)

# --- 3. หน้าตาโปรแกรม ---
st.title("🏎️ KiraCar Pro: Smart Inventory Management")

# โหลดข้อมูลมาแสดง
@st.cache_data(ttl=60)
def load_data():
    try:
        df_raw = pd.read_csv(SHEET_CSV_URL)
        return df_raw
    except:
        return pd.DataFrame()

df = load_data()

menu = st.sidebar.radio("เมนูหลัก", ["📊 Dashboard", "➕ บันทึกรถเข้าใหม่"])

if menu == "📊 Dashboard":
    st.subheader("ตารางคลังรถ")
    st.dataframe(df, use_container_width=True)
    if st.button("🔄 อัปเดตข้อมูล"):
        st.cache_data.clear()
        st.rerun()

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("📋 ลงทะเบียนรถคันใหม่")
    with st.form("car_form", clear_on_submit=True):
        # ตั้งชื่อตัวแปรให้ชัดเจน (ห้ามซ้ำกับชื่อคอลัมน์)
        in_model = st.text_input("ชื่อรุ่นรถ/ปี")
        
        c1, c2 = st.columns(2)
        with c1:
            in_buy = st.number_input("ราคาทุนซื้อ", min_value=0)
            in_status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "จองแล้ว", "ขายแล้ว"])
        with c2:
            in_repair = st.number_input("ค่าซ่อม", min_value=0)
            in_sell = st.number_input("ราคาขาย", min_value=0)
            
        btn_save = st.form_submit_button("🚀 บันทึกข้อมูล")

        if btn_save:
            if in_model:
                with st.spinner('กำลังเชื่อมต่อกับฐานข้อมูล...'):
                    # เรียกใช้ฟังก์ชันและรับผลลัพธ์
                    is_ok, msg = save_to_google_form(in_model, in_buy, in_repair, in_status, in_sell)
                    
                    if is_ok:
                        st.success(f"บันทึก {in_model} เรียบร้อยแล้ว! ข้อมูลจะเข้า Google Sheets ทันที")
                        st.balloons()
                    else:
                        st.error(f"บันทึกไม่สำเร็จ: {msg}")
                        st.info("ตรวจสอบว่าคุณใส่ 'requests' ในไฟล์ requirements.txt หรือยัง?")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")
