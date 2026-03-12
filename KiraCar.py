import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- CONFIG ---
# ใช้ URL แบบปกติ ไม่ต้องเติม time.time() ท้าย URL เพื่อป้องกันการ Loop
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="KiraCar Enterprise AI", layout="wide", page_icon="🚀")

# --- LOAD DATA ---
@st.cache_data(ttl=60) # ตั้งให้ดึงข้อมูลใหม่ทุก 60 วินาที เพื่อความเสถียร
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty: return pd.DataFrame()
        
        # จัดการข้อมูลเบื้องต้น
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        for col in ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).fillna(0)
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0)
        return data
    except Exception as e:
        return pd.DataFrame()

# โหลดข้อมูลมาพักไว้ในตัวแปร
df = load_full_data()

# --- SIDEBAR ---
st.sidebar.title("🚀 KiraCar Enterprise")
# เพิ่มปุ่ม Refresh ข้อมูลด้วยตัวเอง (Manual) เพื่อลดการ Auto-reload
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เมนู", ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า", "🗑️ ลบข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "💎 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    if not df.empty:
        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f}")
        sold_cars = df[df['สถานะ']=='ขายแล้ว']
        cols[1].metric("⏱️ ปิดการขายเฉลี่ย", f"{sold_cars['อายุสต็อก'].mean():.1f} วัน" if not sold_cars.empty else "0 วัน")
        total_inv = df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()
        cols[2].metric("📦 สินค้าคงคลัง", f"{total_inv:,.0f}")
        win_rate = (len(sold_cars) / len(df) * 100) if len(df)>0 else 0
        cols[3].metric("📈 อัตราการขาย", f"{win_rate:.1f}%")

# --- 2. อัปเดตสถานะรถ ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 เปลี่ยนสถานะรถ")
    if not df.empty:
        options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        selection = st.selectbox("เลือกรถ:", options)
        tid = selection.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            new_status = st.selectbox("สถานะใหม่:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], index=["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(row['สถานะ']) if row['สถานะ'] in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0)
            new_sell = st.number_input("ราคาขาย", value=float(row['ราคาขาย']))
            new_fix = st.number_input("ค่าซ่อม", value=float(row['ค่าซ่อม']))
            new_note = st.text_area("หมายเหตุ", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึก"):
                total = float(row['ต้นทุนซื้อ']) + new_fix
                profit = new_sell - total if new_status == "ขายแล้ว" else 0
                payload = {"action": "update", "id": tid, "status": new_status, "fix": new_fix, "total_cost": total, "sell": new_sell, "profit": profit, "note": new_note}
                try:
                    requests.post(SCRIPT_URL, json=payload)
                    st.success("อัปเดตเรียบร้อย!")
                    st.cache_data.clear() # ล้าง Cache เพื่อให้โหลดใหม่หลังบันทึก
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("การเชื่อมต่อล้มเหลว")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 บันทึกรถใหม่")
    with st.form("add_car"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเบื้องต้น", min_value=0)
        sell = st.number_input("ราคาขายเป้าหมาย", min_value=0)
        status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย"])
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total = buy + fix
            profit = sell - total
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d"), "", "", "B"]
            requests.post(SCRIPT_URL, json=data)
            st.cache_data.clear()
            st.success("บันทึกแล้ว!")
            time.sleep(1)
            st.rerun()

# --- เมนูอื่นๆ (ลบข้อมูล/ค้นหา) ใส่โครงไว้สั้นๆ เพื่อความเสถียร ---
elif menu == "🔍 ค้นหา & วิเคราะห์":
    st.write(df)
elif menu == "🗑️ ลบข้อมูล":
    st.info("เลือก ID ที่ต้องการลบใน Google Sheets หรือส่งคำสั่ง Delete (ฟีเจอร์นี้แนะนำให้ใช้ผ่าน Sheets เพื่อความปลอดภัย)")
