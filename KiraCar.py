import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# ใช้ URL แบบ Static เพื่อหยุด Loop การ Rerun
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache ป้องกันการโหลดซ้ำซ้อน) ---
@st.cache_data(ttl=60) 
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # แปลงข้อมูลตัวเลขให้ถูกต้องป้องกัน Error เวลาคำนวณ
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")
if st.sidebar.button("🔄 Sync ข้อมูลใหม่ (Manual)"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เมนู", ["📊 ดูสต็อก", "🔄 อัปเดตสถานะ/ขายรถ", "📥 บันทึกรถเข้าใหม่"])

# --- 1. ดูสต็อก ---
if menu == "📊 ดูสต็อก":
    st.title("📊 รายการสต็อกปัจจุบัน")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลในระบบ")

# --- 2. อัปเดตสถานะ (เน้นแก้คอลัมน์ F ให้มีข้อมูล) ---
elif menu == "🔄 อัปเดตสถานะ/ขายรถ":
    st.title("🔄 อัปเดตสถานะและคำนวณต้นทุนรวม")
    if not df.empty:
        # สร้างตัวเลือกชื่อรถ
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถ:", car_list)
        tid = selected.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], 
                                         index=["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(row['สถานะ']) if row['สถานะ'] in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0)
                new_sell = st.number_input("ราคาขายจริง", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อมรวม (ปรับปรุง)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ บันทึกการเปลี่ยนแปลง"):
                # --- คำนวณต้นทุนรวม (F) ---
                buy_price = float(row['ต้นทุนซื้อ'])
                total_cost = buy_price + new_fix 
                
                # คอลัมน์ H (กำไร) ส่งเป็นค่าว่างตามโจทย์
                profit = "" 
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost, # ส่งค่า F ไปบันทึก
                    "sell": new_sell,
                    "profit": profit,         # คอลัมน์ H ว่างไว้
                    "note": new_note
                }
                
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.success(f"อัปเดต ID {tid} สำเร็จ! ต้นทุนรวมใหม่คือ {total_cost:,.0f} ฿")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                except:
                    st.error("การเชื่อมต่อขัดข้อง กรุณาลองใหม่อีกครั้ง")

# --- 3. บันทึกรถเข้าใหม่ ---
elif menu == "📥 บันทึกรถเข้าใหม่":
    st.title("📥 ลงทะเบียนรถใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ราคาทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            # --- คำนวณต้นทุนรวม (F) ---
            total = buy + fix 
            profit = "" # คอลัมน์ H ว่างไว้
            
            # ลำดับข้อมูล A-L (ID, ชื่อ, สถานะ, ทุนซื้อ, ค่าซ่อม, ต้นทุนรวม(F), ราคาขาย, กำไร(H), ...)
            new_car_data = [
                len(df)+1, name, "กำลังซ่อม", buy, fix, 
                total,  # คอลัมน์ F จะได้รับค่าไปทันที
                sell, 
                profit, 
                datetime.now().strftime("%Y-%m-%d"), "", "", "B"
            ]
            
            try:
                requests.post(SCRIPT_URL, json=new_car_data, timeout=10)
                st.success("บันทึกเรียบร้อย! คอลัมน์ F มีข้อมูลแล้ว")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            except:
                st.error("ส่งข้อมูลไม่สำเร็จ")
