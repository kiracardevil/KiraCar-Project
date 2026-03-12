import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

@st.cache_data(ttl=60)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        return data
    except:
        return pd.DataFrame()

df = load_data()

st.sidebar.title("💎 KiraCar ERP")
if st.sidebar.button("🔄 Sync ข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เมนู", ["📊 ดูสต็อก", "🔄 อัปเดตสถานะ/ขายรถ", "📥 บันทึกรถเข้าใหม่"])

# --- ส่วนที่ 2: อัปเดตสถานะ (เน้นแก้คอลัมน์ F) ---
if menu == "🔄 อัปเดตสถานะ/ขายรถ":
    st.title("🔄 อัปเดตข้อมูลรถ")
    if not df.empty:
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถ:", car_list)
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], index=0)
            new_sell = st.number_input("ราคาขายจริง", value=float(row['ราคาขาย'] if pd.notna(row['ราคาขาย']) else 0))
            new_fix = st.number_input("ค่าซ่อมรวม", value=float(row['ค่าซ่อม'] if pd.notna(row['ค่าซ่อม']) else 0))
            
            if st.form_submit_button("✅ บันทึก"):
                # 1. คำนวณต้นทุนรวม (F)
                buy_price = float(row['ต้นทุนซื้อ'] if pd.notna(row['ต้นทุนซื้อ']) else 0)
                total_cost = buy_price + new_fix 
                
                # 2. กำไร (H) - ส่งเป็นค่าว่างตามที่คุณต้องการ
                profit = "" 
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost, # ส่งค่า F ไปบันทึก
                    "sell": new_sell,
                    "profit": profit,     # ส่งค่าว่างไปที่ H
                    "note": "อัปเดตผ่านระบบ"
                }
                requests.post(SCRIPT_URL, json=payload)
                st.success("บันทึกสำเร็จ! คอลัมน์ F (ต้นทุนรวม) ได้รับการอัปเดตแล้ว")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# --- ส่วนที่ 3: บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถใหม่":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุน")
        fix = st.number_input("ค่าซ่อมเริ่มต้น")
        sell = st.number_input("ราคาขายตั้งเป้า")
        
        if st.form_submit_button("🚀 บันทึก"):
            total = buy + fix # คำนวณคอลัมน์ F
            profit = ""       # ส่งเป็นค่าว่างไปก่อน
            
            # ลำดับข้อมูล A-L (ID, ชื่อ, สถานะ, ทุนซื้อ, ค่าซ่อม, ต้นทุนรวม(F), ราคาขาย, กำไร(H), ...)
            data = [
                len(df)+1, name, "กำลังซ่อม", buy, fix, 
                total,  # คอลัมน์ F
                sell, 
                profit, # คอลัมน์ H
                datetime.now().strftime("%Y-%m-%d"), "", "", "B"
            ]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกเข้าระบบแล้ว! (คอลัมน์ F มีข้อมูลแล้ว)")
            st.cache_data.clear()
            st.rerun()

# --- ส่วนที่ 1: ดูสต็อก ---
elif menu == "📊 ดูสต็อก":
    st.title("📊 รายการสต็อกปัจจุบัน")
    st.dataframe(df, use_container_width=True)
