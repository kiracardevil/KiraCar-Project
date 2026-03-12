import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG (อัปเดต URL ใหม่ที่คุณให้มา) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxSuqMXP6sAXrf7oQPz1psUuBJRqpCcghAte_ePj-vU1J1NVVevomPr3vWRpTHjM6rSJg/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# ฟังก์ชันดึงข้อมูลแบบสด (Direct) - ไม่ใช้ Cache เพื่อป้องกัน Loop
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame()

# --- UI ส่วนหัว ---
st.title("🏎️ KiraCar ERP System")
st.markdown("---")

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("เมนูหลัก", ["📊 ดูสต็อกรถปัจจุบัน", "🔄 อัปเดตสถานะ/ค่าซ่อม", "📥 บันทึกรถเข้าใหม่"])

# --- 1. ดูสต็อกรถ ---
if menu == "📊 ดูสต็อกรถปัจจุบัน":
    st.subheader("📋 รายการรถทั้งหมดในระบบ")
    df = load_data()
    if not df.empty:
        # แสดงตารางแบบเต็มความกว้าง
        st.dataframe(df, use_container_width=True)
        
        # สรุปภาพรวมสั้นๆ
        c1, c2 = st.columns(2)
        c1.metric("จำนวนรถในระบบ", f"{len(df)} คัน")
        if 'ต้นทุนรวม' in df.columns:
            st.metric("เงินลงทุนรวม (คอลัมน์ F)", f"{df['ต้นทุนรวม'].sum():,.0f} ฿")
    else:
        st.info("กำลังโหลดข้อมูล หรือยังไม่มีรถในระบบ")

# --- 2. อัปเดตสถานะ (ที่โปรแกรมจะคำนวณ F = D + E ให้) ---
elif menu == "🔄 อัปเดตสถานะ/ค่าซ่อม":
    st.subheader("⚙️ แก้ไขข้อมูลรถและคำนวณต้นทุนอัตโนมัติ")
    df = load_data()
    if not df.empty:
        # สร้างตัวเลือกจาก ID และชื่อรถ
        car_options = df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected_car = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_options)
        
        # ดึง ID และข้อมูลแถวนั้นมา
        tid = selected_car.split(" | ")[0]
        row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            st.info(f"รถคันที่เลือก: {row['ยี่ห้อ/รุ่น']} (ทุนซื้อเดิม: {row['ต้นทุนซื้อ']:,.0f} ฿)")
            
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
                new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อมรวมสะสม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("บันทึกเพิ่มเติม", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ บันทึกและคำนวณลงคอลัมน์ F"):
                # --- คำนวณแทนสูตร Excel ---
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost, # ส่งไปลงคอลัมน์ F
                    "sell": new_sell,
                    "profit": "", # กำไรว่างไว้ก่อนตามโจทย์
                    "note": new_note
                }
                
                try:
                    response = requests.post(SCRIPT_URL, json=payload, timeout=10)
                    if response.status_code == 200:
                        st.success(f"อัปเดต ID {tid} สำเร็จ! ระบบคำนวณต้นทุนรวมให้แล้ว: {total_cost:,.0f} ฿")
                        st.balloons()
                    else:
                        st.error("ส่งข้อมูลไม่สำเร็จ กรุณาเช็คการตั้งค่า Apps Script")
                except:
                    st.error("การเชื่อมต่อหมดเวลา (Timeout)")

# --- 3. บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.subheader("🆕 เพิ่มรถคันใหม่ลงฐานข้อมูล")
    df = load_data()
    with st.form("add_car_form"):
        name = st.text_input("ยี่ห้อ/รุ่นรถ")
        buy = st.number_input("ราคาทุนที่ซื้อมา (฿)", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น (฿)", min_value=0)
        sell_target = st.number_input("ราคาขายตั้งเป้า (฿)", min_value=0)
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            if name:
                # คำนวณต้นทุนรวม (F) ทันที
                total = buy + fix
                # ลำดับข้อมูล A-L
                new_data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, sell_target, "", datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
                
                requests.post(SCRIPT_URL, json=new_data)
                st.success(f"บันทึก {name} เรียบร้อยแล้ว! คอลัมน์ F = {total:,.0f}")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")
