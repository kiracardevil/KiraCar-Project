import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG (ใช้ URL แบบคงที่เพื่อหยุดวงจรการ Loop) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar ERP", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache ป้องกันการดึงข้อมูลถี่เกินไป) ---
@st.cache_data(ttl=300) # จำข้อมูลไว้ 5 นาที เพื่อความเสถียร
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # คลีนข้อมูลตัวเลขให้พร้อมคำนวณ
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

# โหลดข้อมูลมาพักไว้ในตัวแปร df
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")

# ปุ่ม Refresh สำหรับกดเมื่อต้องการอัปเดตข้อมูลใหม่จาก Google Sheets
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Sync)"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกเมนู", ["📊 ภาพรวมสต็อก", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้าใหม่"])

# --- 1. ภาพรวมสต็อก ---
if menu == "📊 ภาพรวมสต็อก":
    st.title("📊 สรุปรายการรถในระบบ")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c3.metric("🛠️ กำลังซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูล หรือกำลังเชื่อมต่อฐานข้อมูล...")

# --- 2. อัปเดตสถานะรถ (ฟีเจอร์ที่คุณต้องการใช้งาน) ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 เปลี่ยนสถานะ / บันทึกการขาย")
    if not df.empty:
        # รายชื่อรถให้เลือก
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected_car = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_list)
        
        # ดึง ID ของรถคันที่เลือก
        tid = selected_car.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_car_status"):
            col1, col2 = st.columns(2)
            with col1:
                status_options = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                curr_idx = status_options.index(row['สถานะ']) if row['สถานะ'] in status_options else 0
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", status_options, index=curr_idx)
                new_sell = st.number_input("ราคาขายจริง (฿)", value=float(row['ราคาขาย']))
            
            with col2:
                new_fix = st.number_input("ค่าซ่อมเพิ่มเติม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกการเปลี่ยนแปลง"):
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                profit = new_sell - total_cost if new_status == "ขายแล้ว" else 0
                
                payload = {
                    "action": "update", "id": tid, "status": new_status, 
                    "fix": new_fix, "total_cost": total_cost, 
                    "sell": new_sell, "profit": profit, "note": new_note
                }
                
                try:
                    requests.post(SCRIPT_URL, json=payload, timeout=10)
                    st.success("บันทึกสำเร็จ!")
                    st.cache_data.clear() # ล้างแคชเพื่อให้ข้อมูลใหม่แสดงผลทันที
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("การเชื่อมต่อขัดข้อง กรุณาลองใหม่อีกครั้ง")
    else:
        st.warning("ไม่มีข้อมูลรถให้แก้ไข")

# --- 3. บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.title("📥 บันทึกรถเข้าสต็อก")
    with st.form("add_new_car"):
        name = st.text_input("ยี่ห้อ/รุ่นรถ")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะแรกเข้า", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกเข้าระบบเรียบร้อย!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
