import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# แก้ไข: ตัด &t={time.time()} ออกถาวรเพื่อหยุด Loop
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar ERP", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache แทนการรีโหลดมั่วซั่ว) ---
@st.cache_data(ttl=60) # จำข้อมูลไว้ 1 นาที ไม่ต้องดึงใหม่ทุกวินาที
def load_data():
    try:
        # ดึงข้อมูลจาก Google Sheets
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # แปลงข้อมูลตัวเลขให้ถูกต้อง
        for col in ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

# โหลดข้อมูล
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar System")

# เพิ่มปุ่มรีเฟรชแบบ Manual (กดเองเมื่อต้องการอัปเดต)
if st.sidebar.button("🔄 ดึงข้อมูลใหม่ล่าสุด"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกเมนู", ["📊 ภาพรวมสต็อก", "🔄 แก้ไขสถานะรถ", "📥 บันทึกรถเข้า"])

# --- 1. ภาพรวมสต็อก ---
if menu == "📊 ภาพรวมสต็อก":
    st.title("📊 รายการรถทั้งหมดในระบบ")
    if not df.empty:
        # แสดง Metric สรุป
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c3.metric("🛠️ อยู่ระหว่างซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในฐานข้อมูล")

# --- 2. แก้ไขสถานะรถ (ฟีเจอร์ที่คุณต้องการ) ---
elif menu == "🔄 แก้ไขสถานะรถ":
    st.title("🔄 อัปเดตสถานะและข้อมูลรถ")
    if not df.empty:
        # ค้นหาและเลือกรายชื่อรถ
        options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected = st.selectbox("เลือกรถที่ต้องการดำเนินการ:", options)
        
        # แกะ ID ออกมาเพื่อดึงข้อมูลแถวนั้น
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_list = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                # เลือก index ปัจจุบันของรถคันนั้น
                curr_idx = status_list.index(row['สถานะ']) if row['สถานะ'] in status_list else 0
                new_status = st.selectbox("เปลี่ยนสถานะ:", status_list, index=curr_idx)
                new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
            
            with col2:
                new_fix = st.number_input("ค่าซ่อมที่เกิดขึ้น (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("บันทึกเพิ่มเติม", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกข้อมูล"):
                # คำนวณกำไรใหม่ (ถ้าขายแล้ว)
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
                
                # ส่งไปยัง Google Apps Script
                res = requests.post(SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success("บันทึกสำเร็จ! กำลังรีโหลด...")
                    st.cache_data.clear() # ล้างแคชเพื่อให้เห็นข้อมูลใหม่
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการส่งข้อมูล")
    else:
        st.warning("ไม่มีข้อมูลรถในระบบ")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 ลงทะเบียนรถใหม่")
    with st.form("add_car_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเบื้องต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะแรกเข้า", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            # เตรียม Data 12 คอลัมน์ตามชีท (A-L)
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกสำเร็จ!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
