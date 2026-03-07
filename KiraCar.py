import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# Setup Page
st.set_page_config(page_title="KiraCar Smart System", layout="wide")

# Header
st.title("🚗 KiraCar Management System")
st.write("ระบบจัดการรายรับ-รายจ่าย รถยนต์มือสอง")

# Connect to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
except Exception as e:
    st.error("กรุณาตั้งค่า Secrets สำหรับ Google Sheets ก่อนใช้งาน")
    st.stop()

# Menu Sidebar
menu = st.sidebar.selectbox("เมนู", ["Dashboard", "บันทึกรถเข้าใหม่", "จัดการคลังรถ", "รายงาน"])

if menu == "Dashboard":
    if not df.empty:
        df["กำไรสุทธิ"] = pd.to_numeric(df["กำไรสุทธิ"], errors='coerce').fillna(0)
        c1, c2, c3 = st.columns(3)
        c1.metric("รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c2.metric("กำไรสะสม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c3.metric("ขายแล้ว", f"{len(df[df['สถานะ'] == 'ขายแล้ว'])} คัน")
        
        st.write("---")
        fig = px.pie(df, names='สถานะ', title="สัดส่วนรถในคลัง", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

elif menu == "บันทึกรถเข้าใหม่":
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("รุ่นรถ")
        buy = st.number_input("ราคาทุน", min_value=0)
        fix = st.number_input("ค่าซ่อม", min_value=0)
        stat = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        sell = st.number_input("ราคาขาย", min_value=0)
        
        if st.form_submit_button("บันทึกข้อมูล"):
            new_row = pd.DataFrame([{
                "ID": len(df) + 1,
                "ยี่ห้อ/รุ่น": name,
                "สถานะ": stat,
                "ต้นทุนซื้อ": buy,
                "ค่าซ่อม": fix,
                "ราคาขาย": sell,
                "กำไรสุทธิ": sell - (buy + fix) if sell > 0 else 0,
                "วันที่บันทึก": datetime.now().strftime("%Y-%m-%d")
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("บันทึกสำเร็จ!")
            st.rerun()

elif menu == "จัดการคลังรถ":
    st.subheader("แก้ไขข้อมูลรถในคลัง")
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    if st.button("อัปเดตข้อมูลทั้งหมด"):
        # คำนวณกำไรใหม่ก่อนบันทึก
        edited['กำไรสุทธิ'] = pd.to_numeric(edited['ราคาขาย']) - (pd.to_numeric(edited['ต้นทุนซื้อ']) + pd.to_numeric(edited['ค่าซ่อม']))
        conn.update(data=edited)
        st.success("อัปเดตข้อมูลใน Google Sheets เรียบร้อยแล้ว")
        st.rerun()

elif menu == "รายงาน":
    st.subheader("ดาวน์โหลดรายงาน")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("ดาวน์โหลดไฟล์ CSV", data=csv, file_name="KiraCar_Report.csv")
