import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# ใช้ URL แบบคงที่ เพื่อไม่ให้เกิด Loop
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar ERP", layout="wide", page_icon="🏎️")

# --- LOAD DATA ---
@st.cache_data(ttl=60) # ดึงข้อมูลใหม่ทุก 1 นาที หรือเมื่อมีการสั่ง Clear Cache
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # ทำความสะอาดข้อมูลตัวเลข
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except Exception as e:
        st.error(f"การโหลดข้อมูลขัดข้อง: {e}")
        return pd.DataFrame()

# โหลดข้อมูลมาใช้งาน
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar System")

# ปุ่ม Refresh สำหรับดึงข้อมูลใหม่ทันที (Manual)
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Sync)"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เมนู", ["📊 ภาพรวม", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า"])

# --- 1. ภาพรวม ---
if menu == "📊 ภาพรวม":
    st.title("📊 รายการสต็อกรถยนต์")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c3.metric("🛠️ กำลังซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# --- 2. อัปเดตสถานะรถ ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 เปลี่ยนสถานะ / บันทึกการขาย")
    if not df.empty:
        # สร้างรายชื่อรถให้เลือก
        car_options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected_car = st.selectbox("เลือกรถ:", car_options)
        
        # ดึง ID และข้อมูลแถวที่เลือก
        tid = selected_car.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_car_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_list = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                curr_idx = status_list.index(row['สถานะ']) if row['สถานะ'] in status_list else 0
                new_status = st.selectbox("สถานะใหม่:", status_list, index=curr_idx)
                new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
            
            with col2:
                new_fix = st.number_input("ค่าซ่อม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกข้อมูล"):
                # คำนวณใหม่
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
                
                # ส่งไป Google Sheets
                res = requests.post(SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success("บันทึกเรียบร้อย!")
                    st.cache_data.clear() # ล้างแคชเพื่อให้โหลดใหม่หลังบันทึก
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("การเชื่อมต่อเซิร์ฟเวอร์ผิดพลาด")
    else:
        st.warning("ไม่มีข้อมูลรถให้แก้ไข")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_new_car"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาเป้าหมาย", min_value=0)
        status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            data_to_send = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data_to_send)
            st.success("บันทึกสำเร็จ!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

