import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG (ใช้ข้อมูลแบบคงที่เพื่อให้แอปนิ่ง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache ป้องกันการโหลดซ้ำซ้อน) ---
@st.cache_data(ttl=300) # จำข้อมูลไว้ 5 นาที เพื่อความเสถียร
def load_data():
    try:
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

# โหลดข้อมูลมาพักไว้
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")

# ปุ่ม Refresh สำหรับดึงข้อมูลใหม่ (Manual Sync)
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Sync)"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกเมนู", ["📊 ภาพรวมสต็อก", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า"])

# --- 1. ภาพรวมสต็อก ---
if menu == "📊 ภาพรวมสต็อก":
    st.title("📊 รายการรถในระบบ")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถทั้งหมด", f"{len(df)} คัน")
        c3.metric("🛠️ กำลังซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ หรือกำลังโหลด...")

# --- 2. อัปเดตสถานะรถ (ฟีเจอร์หลัก) ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 เปลี่ยนสถานะรถ")
    if not df.empty:
        # รายชื่อรถให้เลือก
        options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected = st.selectbox("เลือกรถที่ต้องการดำเนินการ:", options)
        
        # ดึง ID ออกมา
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_list = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                curr_idx = status_list.index(row['สถานะ']) if row['สถานะ'] in status_list else 0
                new_status = st.selectbox("สถานะใหม่:", status_list, index=curr_idx)
                new_sell = st.number_input("ราคาขายจริง (฿)", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกข้อมูล"):
                total_cost = float(row['ต้นทุนซื้อ']) + new_fix
                profit = new_sell - total_cost if new_status == "ขายแล้ว" else 0
                
                payload = {
                    "action": "update", "id": tid, "status": new_status, 
                    "fix": new_fix, "total_cost": total_cost, 
                    "sell": new_sell, "profit": profit, "note": new_note
                }
                
                try:
                    requests.post(SCRIPT_URL, json=payload, timeout=10)
                    st.success("บันทึกเรียบร้อย!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("การส่งข้อมูลขัดข้อง กรุณาลองใหม่")
    else:
        st.warning("ไม่มีข้อมูลให้แก้ไข")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุน", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะแรกเข้า", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกแล้ว!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
