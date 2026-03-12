import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
SCRIPT_URL = "ใส่ URL ที่ได้จากขั้นตอนที่ 1 ที่นี่"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide")

def load_data():
    return pd.read_csv(SHEET_URL)

st.title("🏎️ KiraCar ERP")

menu = st.sidebar.selectbox("เมนู", ["📊 ดูสต็อก", "🔄 อัปเดตสถานะ (คำนวณทุน)", "📥 บันทึกรถใหม่"])

if menu == "📊 ดูสต็อก":
    df = load_data()
    st.dataframe(df, use_container_width=True)

elif menu == "🔄 อัปเดตสถานะ (คำนวณทุน)":
    df = load_data()
    car_list = df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
    selected = st.selectbox("เลือกรถ:", car_list)
    tid = selected.split(" | ")[0]
    row = df[df['ID'].astype(str) == tid].iloc[0]

    with st.form("edit_form"):
        new_status = st.selectbox("สถานะ:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], index=0)
        new_fix = st.number_input("ค่าซ่อมรวม (฿)", value=float(row['ค่าซ่อม']))
        new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
        
        if st.form_submit_button("✅ บันทึกและคำนวณ"):
            # คำนวณคอลัมน์ F ที่นี่แทน Excel
            total_cost = float(row['ต้นทุนซื้อ']) + new_fix
            
            payload = {
                "action": "update", "id": tid, "status": new_status,
                "fix": new_fix, "total_cost": total_cost, "sell": new_sell
            }
            requests.post(SCRIPT_URL, json=payload)
            st.success(f"บันทึกแล้ว! ต้นทุนรวม (F) = {total_cost:,.0f}")
            st.info("กรุณากดเมนู 'ดูสต็อก' เพื่อดูข้อมูลใหม่")

elif menu == "📥 บันทึกรถใหม่":
    df = load_data()
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ")
        fix = st.number_input("ค่าซ่อมเริ่มแรก")
        if st.form_submit_button("🚀 ลงทะเบียน"):
            total = buy + fix
            data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, 0, "", datetime.now().strftime("%Y-%m-%d")]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกรถใหม่เรียบร้อย!")
