import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="KiraCar Pro", layout="wide", page_icon="🚗")

# 1. URL สำหรับส่งข้อมูล (แกะจากลิงก์ที่คุณส่งมา)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"

# 2. ลิงก์ CSV ของ Google Sheets (วิธีเอา: ไฟล์ > แชร์ > เผยแพร่ไปยังเว็บ > เลือก CSV)
# ** อย่าลืมเอาลิงก์ CSV มาใส่ตรงนี้นะครับ **
SHEET_CSV_URL = "ใส่_URL_CSV_ของคุณที่นี่"

def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
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
    df = pd.read_csv(SHEET_CSV_URL)
except:
    df = pd.DataFrame(columns=["Timestamp", "รุ่นรถ", "ราคาทุน", "ค่าซ่อม", "สถานะ", "ราคาขาย"])

# เมนู Sidebar
menu = st.sidebar.radio("เมนูหลัก", ["📊 Dashboard", "➕ บันทึกรถเข้าใหม่"])

if menu == "📊 Dashboard":
    st.subheader("ภาพรวมธุรกิจ")
    if not df.empty:
        # พยายามเปลี่ยนข้อมูลเป็นตัวเลขเพื่อคำนวณ
        buy_col = df.columns[2]   # คอลัมน์ราคาทุน (ปกติลำดับที่ 3 ใน Sheets)
        repair_col = df.columns[3] # คอลัมน์ค่าซ่อม
        sell_col = df.columns[5]   # คอลัมน์ราคาขาย
        
        df[buy_col] = pd.to_numeric(df[buy_col], errors='coerce').fillna(0)
        df[repair_col] = pd.to_numeric(df[repair_col], errors='coerce').fillna(0)
        df[sell_col] = pd.to_numeric(df[sell_col], errors='coerce').fillna(0)
        
        profit = df[sell_col].sum() - (df[buy_col].sum() + df[repair_col].sum())

        col1, col2, col3 = st.columns(3)
        col1.metric("รถทั้งหมดในระบบ", f"{len(df)} คัน")
        col2.metric("กำไรสะสม (บาท)", f"{profit:,.0f} ฿")
        col3.metric("อัปเดตล่าสุด", datetime.now().strftime("%H:%M"))

        st.write("### รายการรถยนต์ล่าสุด")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ เริ่มบันทึกรถคันแรกได้ที่เมนูซ้ายมือครับ")

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("เพิ่มข้อมูลรถยนต์")
    with st.form("car_form", clear_on_submit=True):
        model = st.text_input("รุ่นรถ (เช่น Honda Civic)")
        buy = st.number_input("ราคาทุน (บาท)", min_value=0)
        repair = st.number_input("ค่าซ่อม (บาท)", min_value=0)
        status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        sell = st.number_input("ราคาขาย (บาท)", min_value=0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            if model:
                if save_to_google_form(model, buy, repair, status, sell):
                    st.success(f"บันทึก {model} เรียบร้อย! ข้อมูลจะแสดงผลในตารางภายใน 1-2 นาที")
                else:
                    st.error("เกิดข้อผิดพลาดในการส่งข้อมูล")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")
