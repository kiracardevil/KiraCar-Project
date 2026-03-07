import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="KiraCar Pro", layout="wide", page_icon="🚗")

# 1. URL สำหรับส่งข้อมูล (เชื่อมกับ Google Form ของคุณ)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"

# 2. URL สำหรับดึงข้อมูลมาแสดง (เชื่อมกับ Google Sheets ของคุณ)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRTaXnMfRxy-JdgCp4rCqJzdUES16l77D8_Okbf-bQnjxnu5HeRyS5agIokGCfG_3x3oCK7VCdlGXG2/pub?gid=754879556&single=true&output=csv"

def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
    # รหัส entry ที่แกะจากลิงก์ฟอร์มของคุณ
    payload = {
        "entry.1392091793": model,       # รุ่นรถ
        "entry.1772417832": buy_price,   # ราคาทุน
        "entry.499287053": repair_cost,  # ค่าซ่อม
        "entry.50844596": status,        # สถานะ
        "entry.1300688537": sell_price,  # ราคาขาย
    }
    try:
        requests.post(FORM_URL, data=payload)
        return True
    except:
        return False

# --- ส่วนหน้าตาโปรแกรม ---
st.title("🚗 KiraCar Management System")
st.markdown("---")

# ดึงข้อมูลมาแสดง
try:
    # อ่านข้อมูลและตั้งชื่อคอลัมน์ให้สวยงาม
    df = pd.read_csv(SHEET_CSV_URL)
    # ลบแถวที่ว่าง (ถ้ามี)
    df = df.dropna(subset=[df.columns[1]]) 
except:
    df = pd.DataFrame()

# เมนู Sidebar
menu = st.sidebar.radio("เมนูหลัก", ["📊 Dashboard", "➕ บันทึกรถเข้าใหม่"])

if menu == "📊 Dashboard":
    st.subheader("ภาพรวมธุรกิจ")
    if not df.empty:
        # พยายามแปลงข้อมูลเป็นตัวเลขเพื่อคำนวณกำไร
        try:
            # สมมติลำดับคอลัมน์จาก Form: [0]Timestamp, [1]รุ่นรถ, [2]ทุน, [3]ซ่อม, [4]สถานะ, [5]ขาย
            buy = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(0)
            repair = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
            sell = pd.to_numeric(df.iloc[:, 5], errors='coerce').fillna(0)
            
            total_profit = sell.sum() - (buy.sum() + repair.sum())
            total_cars = len(df)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("รถในระบบทั้งหมด", f"{total_cars} คัน")
            col2.metric("กำไรสะสม (ประมาณการ)", f"{total_profit:,.0f} ฿")
            col3.metric("อัปเดตข้อมูลเมื่อ", datetime.now().strftime("%H:%M น."))
        except:
            st.warning("กำลังคำนวณข้อมูล...")

        st.write("### 📋 รายการรถยนต์ในคลัง")
        st.dataframe(df, use_container_width=True)
        
        if st.button("🔄 รีเฟรชข้อมูล"):
            st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ เริ่มบันทึกรถคันแรกได้ที่เมนู 'บันทึกรถเข้าใหม่' ครับ")

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("เพิ่มข้อมูลรถยนต์")
    with st.form("car_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            model = st.text_input("ชื่อรุ่นรถ (ยี่ห้อ/รุ่น)", placeholder="เช่น Toyota Fortuner")
            buy = st.number_input("ราคาทุนซื้อ (บาท)", min_value=0, step=1000)
            repair = st.number_input("ค่าซ่อม/ปรับสภาพ (บาท)", min_value=0, step=500)
        with col2:
            status = st.selectbox("สถานะปัจจุบัน", ["กำลังซ่อม", "พร้อมขาย", "จองแล้ว", "ขายแล้ว"])
            sell = st.number_input("ราคาตั้งขาย (บาท)", min_value=0, step=1000)
        
        if st.form_submit_button("✅ บันทึกข้อมูล"):
            if model:
                if save_to_google_form(model, buy, repair, status, sell):
                    st.success(f"บันทึกข้อมูล {model} สำเร็จ!")
                    st.info("💡 หมายเหตุ: ข้อมูลจะใช้เวลาประมาณ 1-2 นาที ในการอัปเดตขึ้นหน้า Dashboard ตามรอบของ Google Sheets")
                else:
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถก่อนกดบันทึก")

# ส่วนท้าย
st.sidebar.markdown("---")
st.sidebar.write("💻 พัฒนาโดย KiraCar Pro System")
