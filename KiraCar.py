import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time  # <--- เพิ่มบรรทัดที่ 5: นำเข้า time เพื่อใช้สุ่มลิงก์
# 1. ตั้งค่า URL (ใช้ตัวที่คุณส่งมาให้)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzDCoF0_s2xNegdr_AImYaF1ZZauURohOsQuwG75Tn2fio_ZyZfua4pgLy3mrIcVkbuHQ/exec"

# 2. ตั้งค่าการอ่านข้อมูล (เปลี่ยนเฉพาะ ID ให้ตรงกับไฟล์ Google Sheets ของคุณ)
# ให้ก๊อปปี้รหัสยาวๆ ในลิงก์ Google Sheets ของคุณมาใส่ตรง SHEET_ID นี้ครับ
# แก้ไขบรรทัดที่ 11 เป็นแบบนี้เป๊ะๆ นะครับ
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🚗")

st.title("🚗 KiraCar Management System")
st.markdown("---")

# ส่วนดึงข้อมูลมาแสดง
try:
    df = pd.read_csv(SHEET_URL)
except:
    df = pd.DataFrame(columns=["ID", "ยี่ห้อ/รุ่น", "สถานะ", "ต้นทุนซื้อ", "ค่าซ่อม", "ราคาขาย", "กำไรสุทธิ", "วันที่บันทึก"])

menu = st.sidebar.selectbox("เมนูการใช้งาน", ["📊 Dashboard", "➕ บันทึกรถเข้าใหม่"])

if menu == "📊 Dashboard":
    if not df.empty:
        # คำนวณกำไรสะสม
        total_profit = pd.to_numeric(df["กำไรสุทธิ"], errors='coerce').sum()
        st.metric("กำไรสะสมทั้งหมด", f"{total_profit:,.0f} บาท")
        
        st.subheader("รายการรถในระบบ")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ ลองไปที่เมนู 'บันทึกรถเข้าใหม่' เพื่อเริ่มใช้งานครับ")

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("กรอกรายละเอียดรถยนต์")
    with st.form("add_car_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ยี่ห้อ / รุ่นรถ")
            buy_price = st.number_input("ราคาทุนซื้อมา", min_value=0, step=1000)
            fix_price = st.number_input("ค่าซ่อม/ปรับสภาพ", min_value=0, step=500)
        with col2:
            status = st.selectbox("สถานะปัจจุบัน", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell_price = st.number_input("ราคาขาย (ถ้ายังไม่ขายให้ใส่ 0)", min_value=0, step=1000)
            
        submit = st.form_submit_button("💾 บันทึกข้อมูลลง Google Sheets")
        
        if submit:
            if name:
                # คำนวณกำไรเบื้องต้น
                profit = sell_price - (buy_price + fix_price) if sell_price > 0 else 0
                
                # เตรียมข้อมูลส่งเข้า Apps Script (ลำดับต้องตรงกับหัวตารางใน Sheets)
                new_data = [
                    len(df) + 1, 
                    name, 
                    status, 
                    buy_price, 
                    fix_price, 
                    sell_price, 
                    profit, 
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ]
                
                # ส่งข้อมูลด้วย requests
                try:
                    with st.spinner('กำลังบันทึกข้อมูล...'):
                        res = requests.post(SCRIPT_URL, json=new_data)
                    
                    if "Success" in res.text:
                        st.success(f"✅ บันทึกข้อมูลรถ {name} เรียบร้อยแล้ว!")
                        st.balloons()
                    else:
                        st.error("❌ บันทึกไม่สำเร็จ: " + res.text)
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถด้วยครับ")


