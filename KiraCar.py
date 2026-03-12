import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide")

# ฟังก์ชันดึงข้อมูล (แบบไม่ใช้ Cache ถ้าแอปยังล่มอยู่)
def load_data_direct():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame()

st.title("🏎️ KiraCar ERP")

# --- SIDEBAR ---
menu = st.sidebar.radio("เมนูใช้งาน", ["📊 ดูตารางรถ", "🔄 อัปเดตสถานะ (คำนวณทุน)", "📥 บันทึกรถใหม่"])

# --- 1. ดูตารางรถ ---
if menu == "📊 ดูตารางรถ":
    df = load_data_direct()
    if not df.empty:
        st.dataframe(df)
    else:
        st.error("ไม่สามารถโหลดข้อมูลได้ หรือตารางว่างเปล่า")

# --- 2. อัปเดตสถานะ (คำนวณ F = D + E) ---
elif menu == "🔄 อัปเดตสถานะ (คำนวณทุน)":
    df = load_data_direct()
    if not df.empty:
        # ดึงรายชื่อมาให้เลือก
        car_list = df.apply(lambda x: f"{x['ID']} - {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        choice = st.selectbox("เลือกรถ:", car_list)
        tid = choice.split(" - ")[0]
        row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("edit_form"):
            new_status = st.selectbox("สถานะ:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            new_fix = st.number_input("ค่าซ่อมสะสม (฿)", value=float(row['ค่าซ่อม']))
            new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
            
            if st.form_submit_button("บันทึกข้อมูล"):
                # คำนวณต้นทุนรวม (F) ส่งไปแทนสูตร Excel
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost,
                    "sell": new_sell,
                    "profit": "",
                    "note": "Update via App"
                }
                requests.post(SCRIPT_URL, json=payload)
                st.success(f"บันทึกสำเร็จ! ต้นทุนรวม (F) = {total_cost:,.0f}")
                st.info("กรุณาเปลี่ยนเมนูเพื่อรีเฟรชข้อมูล")

# --- 3. บันทึกรถใหม่ ---
elif menu == "📥 บันทึกรถใหม่":
    df = load_data_direct()
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ")
        fix = st.number_input("ค่าซ่อมเริ่มแรก")
        if st.form_submit_button("ลงทะเบียนรถ"):
            total = buy + fix # คำนวณ F
            data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, 0, "", datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกรถใหม่เรียบร้อย!")
