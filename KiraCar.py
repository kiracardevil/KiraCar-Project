import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
# ใช้ URL ใหม่ที่คุณเพิ่งส่งมา
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxSA7WWKGDneJk-CU9WaQs99quv_a5NdHPvbMm1mqSGxCNy8zYvUvfiuIynm2tp5N-G/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar System", layout="wide", page_icon="🏎️")

# ฟังก์ชันดึงข้อมูล (ดึงสดทุกครั้งที่เปลี่ยนเมนู เพื่อป้องกัน Loop)
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        return pd.DataFrame()

st.title("🏎️ KiraCar ERP")

# --- SIDEBAR MENU ---
menu = st.sidebar.radio("เมนูใช้งาน", ["📊 ดูสต็อกรถ", "🔄 อัปเดตสถานะ/ทุนรวม", "📥 บันทึกรถใหม่"])

# --- 1. ดูสต็อกรถ ---
if menu == "📊 ดูสต็อกรถ":
    st.subheader("📋 รายการรถปัจจุบัน")
    df = load_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูล หรือกำลังโหลด...")

# --- 2. อัปเดตสถานะ (ที่โปรแกรมจะคำนวณ F = D + E ให้) ---
elif menu == "🔄 อัปเดตสถานะ/ทุนรวม":
    st.subheader("⚙️ แก้ไขข้อมูลและคำนวณต้นทุน")
    df = load_data()
    if not df.empty:
        car_options = df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_options)
        
        tid = selected.split(" | ")[0]
        row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
                new_sell = st.number_input("ราคาขายจริง (฿)", value=float(row['ราคาขาย'] if pd.notna(row['ราคาขาย']) else 0))
            with col2:
                new_fix = st.number_input("ค่าซ่อมสะสม (฿)", value=float(row['ค่าซ่อม'] if pd.notna(row['ค่าซ่อม']) else 0))
                new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ บันทึกและคำนวณลงคอลัมน์ F"):
                # --- คำนวณแทนสูตร Excel (F = D + E) ---
                buy_price = float(row['ต้นทุนซื้อ'] if pd.notna(row['ต้นทุนซื้อ']) else 0)
                total_cost = buy_price + new_fix
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix,
                    "total_cost": total_cost, # ส่งค่า F ไปลงชีท
                    "sell": new_sell,
                    "profit": "", # กำไรว่างไว้ก่อน
                    "note": new_note
                }
                
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.success(f"อัปเดตสำเร็จ! ต้นทุนรวมใหม่คือ {total_cost:,.0f} ฿")
                        st.info("กรุณาเปลี่ยนไปที่เมนู 'ดูสต็อกรถ' เพื่อรีเฟรชข้อมูล")
                    else:
                        st.error("ส่งข้อมูลไม่สำเร็จ กรุณาเช็คการ Deploy Apps Script")
                except:
                    st.error("การเชื่อมต่อหมดเวลา (Timeout)")

# --- 3. บันทึกรถใหม่ ---
elif menu == "📥 บันทึกรถใหม่":
    st.subheader("📥 บันทึกรถเข้าสต็อก")
    df = load_data()
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่นรถ")
        buy = st.number_input("ราคาทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มแรก", min_value=0)
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            if name:
                total = buy + fix # คำนวณ F ทันที
                # ลำดับข้อมูล A-L (F อยู่ลำดับที่ 6)
                data = [len(df)+1, name, "กำลังซ่อม", buy, fix, total, 0, "", datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
                requests.post(SCRIPT_URL, json=data)
                st.success(f"บันทึก {name} เรียบร้อย! คอลัมน์ F = {total:,.0f}")
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")
