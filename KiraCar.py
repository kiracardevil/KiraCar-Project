import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# ใช้ URL แบบคงที่ เพื่อป้องกันการ Loop ของระบบ
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar Enterprise", layout="wide", page_icon="🚀")

# --- LOAD DATA (ใช้ Cache เพื่อความเสถียร) ---
@st.cache_data(ttl=300) # เก็บข้อมูลไว้ 5 นาที ไม่ต้องโหลดใหม่ทุกวินาที
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # คลีนข้อมูลพื้นฐาน
        for col in ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")

# เพิ่มปุ่มรีเฟรชแบบแมนนวล แทนการอัปเดตอัตโนมัติที่ทำให้ล่ม
if st.sidebar.button("🔄 อัปเดตข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกเมนู", ["📊 แผงควบคุม", "🔍 ค้นหา/วิเคราะห์", "🔄 แก้ไขสถานะรถ", "📥 บันทึกรถเข้า"])

# --- 1. แผงควบคุม ---
if menu == "📊 แผงควบคุม":
    st.title("📊 สรุปภาพรวมธุรกิจ")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรสะสม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("📦 รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c3.metric("📈 รายได้คาดการณ์", f"{df['ราคาขาย'].sum():,.0f} ฿")
        st.divider()
        st.dataframe(df, use_container_width=True)

# --- 2. แก้ไขสถานะรถ (ที่ต้องการ) ---
elif menu == "🔄 แก้ไขสถานะรถ":
    st.title("🔄 อัปเดตสถานะและราคาขาย")
    if not df.empty:
        # สร้างรายชื่อให้เลือก
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected_car = st.selectbox("เลือกรถที่ต้องการดำเนินการ:", car_list)
        
        # ดึงข้อมูลคันที่เลือก
        tid = selected_car.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_options = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                # หาตำแหน่งปัจจุบันของสถานะ
                current_idx = status_options.index(row['สถานะ']) if row['สถานะ'] in status_options else 0
                new_status = st.selectbox("เปลี่ยนเป็นสถานะ:", status_options, index=current_idx)
                new_sell = st.number_input("ราคาขายจริง (฿)", value=float(row['ราคาขาย']))
            
            with col2:
                new_fix = st.number_input("ค่าซ่อมเพิ่มเติม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกการเปลี่ยนแปลง"):
                # คำนวณต้นทุนรวมและกำไรใหม่
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                profit = new_sell - total_cost if new_status == "ขายแล้ว" else 0
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost,
                    "sell": new_sell,
                    "profit": profit,
                    "note": new_note
                }
                
                res = requests.post(SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success("อัปเดตข้อมูลสำเร็จ!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("ยังไม่มีข้อมูลรถในระบบ")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 ลงทะเบียนรถใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะเริ่มต้น", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            # ลำดับข้อมูลตามคอลัมน์ A-L (12 คอลัมน์)
            new_data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=new_data)
            st.success("บันทึกสำเร็จ!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
