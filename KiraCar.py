import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

ตั้งค่าหน้าจอ
st.set_page_config(page_title="KiraCar Smart System", layout="wide")

ส่วนหัว
st.title("🚗 KiraCar Management System")
st.write("ระบบจัดการรายรับ-รายจ่าย รถยนต์มือสอง")

เชื่อมต่อ Google Sheets
try:
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0")
except Exception as e:
st.error("กรุณาตั้งค่า Secrets สำหรับ Google Sheets ก่อนใช้งาน")
st.stop()

เมนู
menu = st.sidebar.selectbox("เมนู", ["Dashboard", "บันทึกรถเข้าใหม่", "จัดการคลังรถ", "รายงาน"])

if menu == "Dashboard":
if not df.empty:
df["กำไรสุทธิ"] = pd.to_numeric(df["กำไรสุทธิ"], errors='coerce').fillna(0)
c1, c2, c3 = st.columns(3)
c1.metric("รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
c2.metric("กำไรสะสม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
c3.metric("ขายแล้ว", f"{len(df[df['สถานะ'] == 'ขายแล้ว'])} คัน")

elif menu == "บันทึกรถเข้าใหม่":
with st.form("add_form", clear_on_submit=True):
name = st.text_input("รุ่นรถ")
buy = st.number_input("ราคาทุน", min_value=0)
fix = st.number_input("ค่าซ่อม", min_value=0)
stat = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
sell = st.number_input("ราคาขาย", min_value=0)

elif menu == "จัดการคลังรถ":
edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
if st.button("บันทึกการแก้ไข"):
edited['กำไรสุทธิ'] = pd.to_numeric(edited['ราคาขาย']) - (pd.to_numeric(edited['ต้นทุนซื้อ']) + pd.to_numeric(edited['ค่าซ่อม']))
conn.update(data=edited)
st.success("อัปเดตเรียบร้อย")
st.rerun()

elif menu == "รายงาน":
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("ดาวน์โหลด CSV", data=csv, file_name="KiraCar_Report.csv")