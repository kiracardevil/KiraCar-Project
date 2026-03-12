import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# แก้ไข: ใช้ URL แบบคงที่เพื่อหยุดวงจรการ Rerun ไม่รู้จบ
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# --- LOAD DATA (ใช้ Cache เพื่อความเสถียร) ---
@st.cache_data(ttl=300) # จำข้อมูลไว้ 5 นาที ไม่ต้องโหลดใหม่ทุกครั้งที่ขยับเมาส์
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        # แปลงข้อมูลตัวเลขให้เป็นตัวเลขจริงๆ
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame()

# โหลดข้อมูลมาพักไว้
df = load_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar ERP")

# ปุ่ม Refresh สำหรับกดเมื่อคุณมีการไปแก้ใน Google Sheets แล้วอยากให้แอปอัปเดต
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด (Sync)"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เมนูบริหารจัดการ", ["📊 ภาพรวมสต็อก", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถใหม่"])

# --- 1. ภาพรวมสต็อก ---
if menu == "📊 ภาพรวมสต็อก":
    st.title("📊 รายการรถในระบบ")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 กำไรรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        c2.metric("🚗 รถในสต็อก", f"{len(df[df['สถานะ'] != 'ขายแล้ว'])} คัน")
        c3.metric("🛠️ กำลังซ่อม", f"{len(df[df['สถานะ'] == 'กำลังซ่อม'])} คัน")
        
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# --- 2. อัปเดตสถานะรถ (ฟีเจอร์หลักที่คุณต้องการ) ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 เปลี่ยนสถานะ / บันทึกการขาย")
    if not df.empty:
        # สร้างรายชื่อรถให้เลือกแบบง่ายๆ
        car_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selected_car = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_list)
        
        # ดึง ID ของรถคันที่เลือก
        tid = selected_car.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_options = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                curr_idx = status_options.index(row['สถานะ']) if row['สถานะ'] in status_options else 0
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", status_options, index=curr_idx)
                new_sell = st.number_input("ราคาขาย (฿)", value=float(row['ราคาขาย']))
            with col2:
                new_fix = st.number_input("ค่าซ่อมเพิ่มเติม (฿)", value=float(row['ค่าซ่อม']))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกการเปลี่ยนแปลง"):
                # คำนวณต้นทุนรวมและกำไรใหม่ก่อนส่ง
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
                
                res = requests.post(SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success("บันทึกสำเร็จ!")
                    st.cache_data.clear() # ล้างแคชเพื่อให้ข้อมูลใหม่แสดงผลทันที
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้")

# --- 3. บันทึกรถใหม่ ---
elif menu == "📥 บันทึกรถใหม่":
    st.title("📥 บันทึกรถเข้าสต็อก")
    with st.form("add_car"):
        name = st.text_input("ยี่ห้อ/รุ่นรถ")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะแรกเข้า", ["กำลังซ่อม", "พร้อมขาย"])
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            total = buy + fix
            profit = sell - total
            # ส่งข้อมูล 12 คอลัมน์ (A-L)
            new_data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=new_data)
            st.success("บันทึกข้อมูลแล้ว!")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
