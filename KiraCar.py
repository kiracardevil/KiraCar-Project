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

# --- 1. ดูสต็อก ---
if menu == "📊 ดูสต็อก":
    st.title("📊 รายการสต็อกปัจจุบัน")
    st.dataframe(df, use_container_width=True)

# --- 2. อัปเดตสถานะ (โปรแกรมคำนวณคอลัมน์ F ให้แทน Excel) ---
elif menu == "🔄 อัปเดตสถานะ/ขายรถ":
    st.title("🔄 อัปเดตข้อมูลรถ")
    if not df.empty:
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถ:", car_list)
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], index=0)
                new_sell = st.number_input("ราคาขายจริง", value=float(row['ราคาขาย'] if pd.notna(row['ราคาขาย']) else 0))
            with col2:
                new_fix = st.number_input("ค่าซ่อมรวม", value=float(row['ค่าซ่อม'] if pd.notna(row['ค่าซ่อม']) else 0))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ บันทึก"):
                # --- [CORE LOGIC] โปรแกรมคำนวณแทนสูตร Excel ---
                buy_price = float(row['ต้นทุนซื้อ'] if pd.notna(row['ต้นทุนซื้อ']) else 0)
                total_cost = buy_price + new_fix # นี่คือสูตร F = D + E
                
                # ถ้ายังไม่อยากยุ่งกับกำไร (H) ให้ส่งเป็นค่าว่างหรือ 0
                profit = "" 
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost, # ส่งไปลงคอลัมน์ F
                    "sell": new_sell,
                    "profit": profit,
                    "note": new_note
                }
                
                requests.post(SCRIPT_URL, json=payload)
                st.success(f"บันทึกสำเร็จ! คำนวณต้นทุนรวมให้แล้ว: {total_cost:,.2f} ฿")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# --- 3. บันทึกรถเข้าใหม่ (คำนวณคอลัมน์ F ตั้งแต่เริ่ม) ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุนซื้อ")
        fix = st.number_input("ค่าซ่อมเริ่มต้น")
        sell = st.number_input("ราคาขายตั้งเป้า")
        
        if st.form_submit_button("🚀 บันทึก"):
            # --- [CORE LOGIC] คำนวณ F = D + E ---
            total = buy + fix 
            
            # ส่งข้อมูลเรียงตาม A-L (คอลัมน์ F คือลำดับที่ 6 ในลิสต์)
            data = [
                len(df)+1, name, "กำลังซ่อม", buy, fix, 
                total,  # คอลัมน์ F
                sell, 
                "",     # คอลัมน์ H (กำไรว่างไว้)
                datetime.now().strftime("%Y-%m-%d"), "", "", "B"
            ]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกเข้าระบบแล้ว! (คำนวณต้นทุนรวมให้เรียบร้อย)")
            st.cache_data.clear()
            st.rerun()
