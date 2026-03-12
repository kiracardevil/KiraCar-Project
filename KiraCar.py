import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# ใช้ URL แบบคงที่ (Static) เพื่อไม่ให้เกิด Loop
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar ERP", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache เพื่อความนิ่ง) ---
@st.cache_data(ttl=60) # ดึงข้อมูลใหม่ทุก 1 นาที หรือเมื่อกดปุ่ม Refresh
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # ทำความสะอาดข้อมูลตัวเลข
        for col in ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar System")

# ปุ่มรีเฟรชข้อมูล (Manual) ป้องกันแอปสับสน
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุดจาก Sheets"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกรายการ", ["📊 สรุปภาพรวม", "🔄 แก้ไขสถานะรถ", "📥 บันทึกรถเข้าใหม่"])

# --- 1. สรุปภาพรวม ---
if menu == "📊 สรุปภาพรวม":
    st.title("📊 ภาพรวมสต็อกรถยนต์")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรสะสม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถทั้งหมด", f"{len(df)} คัน")
        c3.metric("🛠️ กำลังซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลในระบบ")

# --- 2. แก้ไขสถานะรถ (เป้าหมายของคุณ) ---
elif menu == "🔄 แก้ไขสถานะรถ":
    st.title("🔄 อัปเดตสถานะรถ (กำลังซ่อม / พร้อมขาย / ขายแล้ว)")
    if not df.empty:
        # รายชื่อรถให้เลือก
        target_options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} [{x['สถานะ']}]", axis=1).tolist()
        selected = st.selectbox("เลือกรถที่ต้องการเปลี่ยนสถานะ:", target_options)
        
        # ดึง ID ออกมา
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("edit_status_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_list = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                # เลือกสถานะเดิมที่มีอยู่
                current_idx = status_list.index(row['สถานะ']) if row['สถานะ'] in status_list else 0
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", status_list, index=current_idx)
                new_sell = st.number_input("ราคาขาย (บาท)", value=float(row['ราคาขาย']))
            
            with col2:
                new_fix = st.number_input("ค่าซ่อม (บาท)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุเพิ่มเติม", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกการเปลี่ยนแปลง"):
                # คำนวณกำไรและต้นทุนรวมใหม่ทันที
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
                
                # ส่งข้อมูลไป Apps Script
                response = requests.post(SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"อัปเดต {row['ยี่ห้อ/รุ่น']} เรียบร้อย!")
                    st.cache_data.clear() # ล้าง Cache เพื่อให้โหลดข้อมูลใหม่
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")
    else:
        st.warning("ยังไม่มีข้อมูลรถให้แก้ไข")

# --- 3. บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.title("📥 ลงทะเบียนรถใหม่")
    with st.form("new_car_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy_price = st.number_input("ราคาทุนที่ซื้อมา", min_value=0)
        fix_price = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        target_sell = st.number_input("ราคาที่ตั้งขาย", min_value=0)
        initial_status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total = buy_price + fix_price
            profit = target_sell - total
            # บันทึก 12 คอลัมน์ (A-L)
            data_row = [len(df)+1, name, initial_status, buy_price, fix_price, total, target_sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data_row)
            st.success("บันทึกสำเร็จ!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
