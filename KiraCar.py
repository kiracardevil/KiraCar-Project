import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG (ใช้ค่าคงที่ทั้งหมดเพื่อความนิ่ง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache แบบมีกำหนดเวลา) ---
@st.cache_data(ttl=60) # ดึงใหม่ทุก 1 นาทีเท่านั้น ถ้าไม่กดปุ่ม Sync เอง
def load_data():
    try:
        # ดึง CSV จาก Google Sheets
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # ทำความสะอาดข้อมูลตัวเลข
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ', 'ต้นทุนรวม']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except Exception as e:
        return pd.DataFrame()

# เรียกใช้ข้อมูล
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")

# ปุ่ม Sync แบบ Manual ป้องกันแอปสั่ง Rerun เองจนล่ม
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกเมนู", ["📊 ดูสต็อกรถ", "🔄 อัปเดตสถานะ/ขายรถ", "📥 บันทึกรถเข้าใหม่"])

# --- 1. ดูสต็อกรถ ---
if menu == "📊 ดูสต็อกรถ":
    st.title("📊 รายการรถในสต็อกปัจจุบัน")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("กำลังโหลดข้อมูลหรือยังไม่มีข้อมูลในระบบ...")

# --- 2. อัปเดตสถานะ (โปรแกรมคำนวณคอลัมน์ F ให้) ---
elif menu == "🔄 อัปเดตสถานะ/ขายรถ":
    st.title("🔄 อัปเดตข้อมูลรถ")
    if not df.empty:
        # สร้างรายการให้เลือก
        car_options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถที่ต้องการแก้ไข:", car_options)
        
        # ดึงข้อมูลแถวที่เลือก
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_car_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**รุ่น:** {row['ยี่ห้อ/รุ่น']}")
                new_status = st.selectbox("เปลี่ยนสถานะ:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
                new_sell = st.number_input("ราคาขายจริง (฿)", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อมรวมสะสม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            submit = st.form_submit_button("✅ บันทึกการอัปเดต")
            
            if submit:
                # --- คำนวณแทนสูตร Excel ---
                buy_price = float(row['ต้นทุนซื้อ'])
                total_cost = buy_price + new_fix  # คำนวณส่งคอลัมน์ F
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost,
                    "sell": new_sell,
                    "profit": "", # ปล่อยว่างไว้ตามต้องการ
                    "note": new_note
                }
                
                with st.spinner("กำลังส่งข้อมูลไปยัง Google Sheets..."):
                    res = requests.post(SCRIPT_URL, json=payload)
                    if res.status_code == 200:
                        st.success(f"อัปเดตสำเร็จ! ต้นทุนรวมใหม่คือ: {total_cost:,.0f} ฿")
                        st.cache_data.clear()
                        time.sleep(1) # หน่วงเวลาเล็กน้อยให้ Google Sheets ทำงานเสร็จ
                        st.rerun()

# --- 3. บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_car_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix # คำนวณส่งคอลัมน์ F
            # เรียงข้อมูลตาม A-L
            data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, sell, "", datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกสำเร็จ!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
