import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Enterprise AI", layout="wide", page_icon="🚀")

# --- LOAD DATA ---
@st.cache_data(ttl=15) # เพิ่มเวลา Cache เป็น 15 วินาที เพื่อลดภาระเซิร์ฟเวอร์
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty or len(data.columns) < 5:
            return pd.DataFrame()
        
        # คลีนข้อมูลตัวเลข
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0)
        return data
    except Exception as e:
        return pd.DataFrame()

df = load_full_data()

# --- SIDEBAR ---
st.sidebar.title("🚀 KiraCar Enterprise")
# เปลี่ยนเป็น Selectbox เพื่อความเสถียรของ State
menu = st.sidebar.selectbox("เมนูบริหารจัดการ", 
    ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์รถ", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า", "🗑️ ล้างฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "💎 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    if not df.empty:
        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f}", "THB")
        
        sold_df = df[df['สถานะ']=='ขายแล้ว']
        avg_turn = sold_df['อายุสต็อก'].mean() if not sold_df.empty else 0
        cols[1].metric("⏱️ ปิดการขายเฉลี่ย", f"{avg_turn:.1f} วัน")
        
        total_inv = df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()
        cols[2].metric("📦 มูลค่าสินค้าคงคลัง", f"{total_inv:,.0f}", "THB")
        
        win_rate = (len(sold_df) / len(df) * 100) if len(df)>0 else 0
        cols[3].metric("📈 อัตราการขายออก", f"{win_rate:.1f}%")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 กำไรแยกตามเกรด")
            plot_df = df[df['กำไรสุทธิ'] > 0].copy()
            if not plot_df.empty:
                st.plotly_chart(px.sunburst(plot_df, path=['เกรดรถ', 'สถานะ'], values='กำไรสุทธิ'), use_container_width=True)
            else: st.info("ยังไม่มีข้อมูลกำไร")
        with c2:
            st.subheader("🔥 Inventory Velocity")
            if not sold_df.empty:
                brand_speed = sold_df.groupby('ยี่ห้อ/รุ่น')['อายุสต็อก'].mean().sort_values().reset_index()
                st.plotly_chart(px.bar(brand_speed.head(5), x='อายุสต็อก', y='ยี่ห้อ/รุ่น', orientation='h'), use_container_width=True)
            else: st.info("ยังไม่มีข้อมูลการขาย")
    else:
        st.warning("⚠️ ไม่พบข้อมูลในระบบ กรุณาบันทึกรถเข้าก่อน")

# --- 2. ค้นหา & วิเคราะห์รถ ---
elif menu == "🔍 ค้นหา & วิเคราะห์รถ":
    st.title("🔍 ค้นหาและวิเคราะห์รถ")
    search = st.text_input("ค้นหารุ่นรถ...")
    if not df.empty:
        filtered = df[df['ยี่ห้อ/รุ่น'].astype(str).str.contains(search, case=False)] if search else df
        for _, row in filtered.iterrows():
            with st.expander(f"🚗 {row['ยี่ห้อ/รุ่น']} (ID: {row['ID']})"):
                st.write(f"**สถานะ:** {row['สถานะ']} | **ต้นทุนรวม:** {row['ต้นทุนรวม']:,.0f} ฿")
                st.write(f"**กำไร:** {row['กำไรสุทธิ']:,.0f} ฿ ({row['ROI (%)']:.1f}%)")

# --- 3. อัปเดตสถานะรถ ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 อัปเดตสถานะรถยนต์")
    if not df.empty:
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        target = st.selectbox("เลือกรถ:", target_list)
        tid = target.split(" | ")[0].split(": ")[1]
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            status_opt = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
            new_status = st.selectbox("สถานะใหม่:", status_opt, index=status_opt.index(row['สถานะ']) if row['สถานะ'] in status_opt else 0)
            new_sell = st.number_input("ราคาขายจริง", value=float(row['ราคาขาย']))
            new_fix = st.number_input("ค่าซ่อมปรับปรุง", value=float(row['ค่าซ่อม']))
            new_note = st.text_area("หมายเหตุเพิ่มเติม", value=str(row['หมายเหตุ']))
            
            if st.form_submit_button("✅ บันทึกการอัปเดต"):
                total = float(row['ต้นทุนซื้อ']) + new_fix
                profit = new_sell - total if new_status == "ขายแล้ว" else 0
                payload = {"action": "update", "id": tid, "status": new_status, "fix": new_fix, "total_cost": total, "sell": new_sell, "profit": profit, "note": new_note}
                requests.post(SCRIPT_URL, json=payload)
                st.success("บันทึกสำเร็จ!")
                time.sleep(1)
                st.rerun()

# --- 4. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 บันทึกรถเข้า")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ/รุ่น")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        grade = st.select_slider("เกรด", options=["C", "B", "B+", "A", "A+"])
        img = st.text_input("URL รูปภาพ")
        note = st.text_area("หมายเหตุ")
        
        if st.form_submit_button("🚀 บันทึก"):
            total = buy + fix
            profit = sell - total if sell > 0 else 0
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d %H:%M"), img, note, grade]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกข้อมูลแล้ว!")
            time.sleep(1)
            st.rerun()

# --- 5. ลบข้อมูล ---
elif menu == "🗑️ ล้างฐานข้อมูล":
    st.title("🗑️ ลบข้อมูล")
    if not df.empty:
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        target = st.selectbox("เลือกรายการที่ต้องการลบ:", target_list)
        if st.checkbox("ยืนยัน") and st.button("🚨 ลบถาวร"):
            tid = target.split(" | ")[0].split(": ")[1]
            requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
            st.rerun()
