import streamlit as st
import pandas as pd
import requests  # ตัวส่งข้อมูล
from datetime import datetime

# 1. วาง URL ที่ก๊อปมาลงในนี้
SCRIPT_URL = "ใส่_WEB_APP_URL_ที่คุณก๊อปมาตรงนี้"

# 2. ลิงก์อ่านข้อมูล (ใช้ ID จาก Google Sheets ของคุณ)
# เปลี่ยน 'YOUR_SHEET_ID' เป็นรหัสที่อยู่ในลิงก์ Google Sheets ของคุณ
SHEET_ID = "ใส่_ID_ไฟล์_Google_Sheets_ตรงนี้"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide")
st.title("🚗 KiraCar Management System")

# ดึงข้อมูลมาแสดง (อ่านฟรี)
try:
    df = pd.read_csv(SHEET_URL)
except:
    df = pd.DataFrame(columns=["ID", "ยี่ห้อ/รุ่น", "สถานะ", "ต้นทุนซื้อ", "ค่าซ่อม", "ราคาขาย", "กำไรสุทธิ", "วันที่บันทึก"])

menu = st.sidebar.selectbox("เมนู", ["Dashboard", "บันทึกรถเข้าใหม่"])

if menu == "Dashboard":
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

elif menu == "บันทึกรถเข้าใหม่":
    with st.form("add_car", clear_on_submit=True):
        name = st.text_input("รุ่นรถ")
        buy = st.number_input("ราคาทุน", min_value=0)
        fix = st.number_input("ค่าซ่อม", min_value=0)
        stat = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        sell = st.number_input("ราคาขาย", min_value=0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            # เตรียมข้อมูลส่ง
            new_data = [
                len(df) + 1, name, stat, buy, fix, sell, 
                sell - (buy + fix) if sell > 0 else 0, 
                datetime.now().strftime("%Y-%m-%d")
            ]
            
            # ส่งหาเลขา (Apps Script)
            res = requests.post(SCRIPT_URL, json=new_data)
            
            if "Success" in res.text:
                st.success("บันทึกสำเร็จ!")
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดในการบันทึก")
