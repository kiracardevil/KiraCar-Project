import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG (Static Only) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache แบบจำกัดเวลาเพื่อหยุด Loop) ---
@st.cache_data(ttl=300) # ดึงข้อมูลใหม่ทุก 5 นาที หรือเมื่อกดปุ่ม Sync
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty: return pd.DataFrame()
        # ทำความสะอาดข้อมูลตัวเลข
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'ต้นทุนรวม']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")
if st.sidebar.button("🔄 อัปเดตข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.info("ล้างแคชเรียบร้อย กรุณารอสักครู่...")
    time.sleep(1)
    st.rerun()

menu = st.sidebar.selectbox("เมนู", ["📊 ภาพรวมสต็อก", "🔄 แก้ไขสถานะรถ (คำนวณทุนรวม)", "📥 บันทึกรถใหม่"])

# --- 1. ภาพรวมสต็อก ---
if menu == "📊 ภาพรวมสต็อก":
    st.title("📊 รายการสต็อกปัจจุบัน")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("กำลังเชื่อมต่อฐานข้อมูล...")

# --- 2. แก้ไขสถานะรถ (ที่โปรแกรมจะคำนวณ F = D + E ให้) ---
elif menu == "🔄 แก้ไขสถานะรถ (คำนวณทุนรวม)":
    st.title("🔄 อัปเดตข้อมูลและคำนวณต้นทุน")
    if not df.empty:
        car_options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถ:", car_options)
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], 
                                         index=["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(row['สถานะ']) if row['สถานะ'] in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0)
                new_sell = st.number_input("ราคาขายจริง", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อมสะสมทั้งหมด (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ บันทึกและคำนวณต้นทุน"):
                # --- คำนวณแทนสูตร Excel (F = D + E) ---
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                
                payload = {
                    "action": "update", "id": tid, "status": new_status,
                    "fix": new_fix, "total_cost": total_cost, # ส่งค่า F ไปบันทึก
                    "sell": new_sell, "profit": "", "note": new_note
                }
                
                response = requests.post(SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"บันทึกสำเร็จ! ต้นทุนรวมใหม่ (คอลัมน์ F) คือ {total_cost:,.0f} ฿")
                    st.cache_data.clear()
                else:
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")

# --- 3. บันทึกรถใหม่ ---
elif menu == "📥 บันทึกรถใหม่":
    st.title("📥 บันทึกรถเข้าสต็อก")
    with st.form("add_car"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ (฿)", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มแรก (฿)", min_value=0)
        sell = st.number_input("ราคาตั้งขาย (฿)", min_value=0)
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix # คำนวณ F ทันที
            data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, sell, "", datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกสำเร็จ! คอลัมน์ F ถูกเติมข้อมูลแล้ว")
            st.cache_data.clear()
