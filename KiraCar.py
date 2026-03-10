import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px
import plotly.graph_objects as go

# --- Config ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Ultra Pro", layout="wide", page_icon="💎")

# --- Load Data ---
@st.cache_data(ttl=5)
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        # คำนวณต้นทุนรวม
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        # คำนวณ % กำไร (ROI)
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        return data
    except:
        return pd.DataFrame(columns=["ID", "ยี่ห้อ/รุ่น", "สถานะ", "ต้นทุนซื้อ", "ค่าซ่อม", "ราคาขาย", "กำไรสุทธิ", "วันที่บันทึก", "ลิงก์รูปภาพ"])

df = load_data()

# --- Sidebar ---
st.sidebar.markdown("# 💎 KiraCar Ultra")
menu = st.sidebar.selectbox("เมนูควบคุม", ["📊 BI Dashboard", "🔍 คลังรถ & รูปภาพ", "➕ รับรถเข้า", "🗑️ ล้างข้อมูล"])

# --- 1. BI Dashboard ---
if menu == "📊 BI Dashboard":
    st.title("🚀 Business Intelligence Dashboard")
    
    # สรุปภาพรวมแบบตัวเลข
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("กำไรสะสมรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
    with m2:
        avg_roi = df[df['สถานะ']=='ขายแล้ว']['ROI (%)'].mean()
        st.metric("ROI เฉลี่ย (ต่อคัน)", f"{avg_roi:.1f}%")
    with m3:
        st.metric("มูลค่าสต็อกคงเหลือ", f"{df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum():,.0f} ฿")
    with m4:
        st.metric("รถรอขาย", f"{len(df[df['สถานะ']=='พร้อมขาย'])} คัน")

    st.markdown("---")

    # กราฟวิเคราะห์
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 สัดส่วนรถในคลัง")
        fig_pie = px.pie(df, names='สถานะ', hole=0.4, color='สถานะ',
                         color_discrete_map={'พร้อมขาย':'#00CC96', 'กำลังซ่อม':'#FFA15A', 'ขายแล้ว':'#636EFA'})
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        st.subheader("📈 กำไรสะสมรายเดือน")
        df['Month'] = df['วันที่บันทึก'].dt.strftime('%b %Y')
        fig_line = px.line(df.groupby('Month')['กำไรสุทธิ'].sum().reset_index(), x='Month', y='กำไรสุทธิ', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

# --- 2. Search & Photo Gallery ---
elif menu == "🔍 คลังรถ & รูปภาพ":
    st.title("🚗 คลังรถยนต์และรายละเอียด")
    search = st.text_input("🔍 ค้นหาชื่อรุ่นรถ...")
    
    filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False, na=False)]
    
    # โชว์รูปแบบการ์ด
    for i, row in filtered.iterrows():
        with st.expander(f"📌 {row['ยี่ห้อ/รุ่น']} - [ {row['สถานะ']} ]"):
            c1, c2 = st.columns([1, 2])
            with c1:
                # ถ้ามีลิงก์รูปภาพให้โชว์ ถ้าไม่มีโชว์รูป placeholder
                img_url = row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/300x200?text=No+Image"
                st.image(img_url, use_column_width=True)
            with c2:
                st.write(f"**💰 ราคาขาย:** {row['ราคาขาย']:,.0f} บาท")
                st.write(f"**🛠 ต้นทุนรวม:** {row['ต้นทุนรวม']:,.0f} บาท")
                st.write(f"**📈 กำไรคันนี้:** {row['กำไรสุทธิ']:,.0f} บาท ({row['ROI (%)']:.1f}%)")
                st.write(f"📅 บันทึกเมื่อ: {row['วันที่บันทึก']}")
                
                # ระบบปุ่มก๊อปปี้ใบปิดการขาย
                sale_text = f"🚗 ปิดการขาย {row['ยี่ห้อ/รุ่น']}\n💰 ราคา: {row['ราคาขาย']:,.0f}\n✅ สถานะ: {row['สถานะ']}\n📍 KiraCar System"
                st.text_area("ข้อความปิดการขาย (ก๊อปปี้ไปส่ง Line)", sale_text, height=100)

# --- 3. เพิ่มรถ (อัปเกรดให้ใส่ลิงก์รูปได้) ---
elif menu == "➕ รับรถเข้า":
    st.title("➕ ลงทะเบียนรถยนต์ใหม่")
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ยี่ห้อ / รุ่น")
            buy = st.number_input("ราคาทุนซื้อ", min_value=0)
            fix = st.number_input("ค่าซ่อม", min_value=0)
        with col2:
            status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell = st.number_input("ราคาขาย", min_value=0)
            img = st.text_input("🔗 ลิงก์รูปภาพ (URL)")
            
        if st.form_submit_button("🚀 บันทึกเข้าระบบ"):
            if name:
                profit = sell - (buy + fix) if sell > 0 else 0
                new_row = [len(df)+1, name, status, buy, fix, sell, profit, 
                           datetime.now().strftime("%Y-%m-%d %H:%M"), img]
                requests.post(SCRIPT_URL, json=new_row)
                st.success("บันทึกเรียบร้อย!")
                st.balloons()
                time.sleep(1)
                st.rerun()

# --- 4. ลบข้อมูล (แบบเดิม) ---
elif menu == "🗑️ ล้างข้อมูล":
    # ... (โค้ดลบเดิมของคุณ)
    st.title("🗑️ ลบข้อมูล")
    options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
    target = st.selectbox("เลือกรายการที่จะลบ", options)
    if st.button("ยืนยันการลบ"):
        target_id = target.split(" | ")[0].split(": ")[1]
        requests.post(SCRIPT_URL, json={"action": "delete", "id": target_id})
        st.error("ลบเรียบร้อย!")
        st.rerun()
