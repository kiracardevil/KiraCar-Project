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

# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=5)
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['ต้นทุนรวม'] = pd.to_numeric(data['ต้นทุนซื้อ'], errors='coerce').fillna(0) + pd.to_numeric(data['ค่าซ่อม'], errors='coerce').fillna(0)
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_full_data()

# --- SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/741/741407.png", width=100)
st.sidebar.title("KiraCar Enterprise")
# รวมเมนูทั้งหมดไว้ที่นี่ที่เดียว
menu = st.sidebar.radio("เมนูบริหารจัดการ", ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์รถ", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า", "🗑️ ล้างฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "💎 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 ดาวน์โหลดรายงาน Excel (CSV)", data=csv, file_name=f'KiraCar_Report.csv')
        
        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f}", "THB")
        avg_turn = df[df['สถานะ']=='ขายแล้ว']['อายุสต็อก'].mean() if not df[df['สถานะ']=='ขายแล้ว'].empty else 0
        cols[1].metric("⏱️ ปิดการขายเฉลี่ย", f"{avg_turn:.1f} วัน")
        total_inv = df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()
        cols[2].metric("📦 มูลค่าสินค้าคงคลัง", f"{total_inv:,.0f}", "THB")
        win_rate = (len(df[df['สถานะ']=='ขายแล้ว']) / len(df) * 100) if len(df)>0 else 0
        cols[3].metric("📈 อัตราการขายออก", f"{win_rate:.1f}%")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 กำไรแยกตามเกรดรถ (A/B/C)")
            plot_df = df[df['กำไรสุทธิ'] > 0].copy()
            if not plot_df.empty:
                fig = px.sunburst(plot_df, path=['เกรดรถ', 'สถานะ'], values='กำไรสุทธิ', color='เกรดรถ')
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("🔥 Inventory Velocity")
            sold_cars = df[df['สถานะ']=='ขายแล้ว']
            if not sold_cars.empty:
                brand_speed = sold_cars.groupby('ยี่ห้อ/รุ่น')['อายุสต็อก'].mean().sort_values().reset_index()
                st.plotly_chart(px.bar(brand_speed.head(5), x='อายุสต็อก', y='ยี่ห้อ/รุ่น', orientation='h'), use_container_width=True)

# --- 2. ค้นหา & วิเคราะห์รถ ---
elif menu == "🔍 ค้นหา & วิเคราะห์รถ":
    st.title("🔍 ค้นหาและประเมินราคารถ")
    search = st.text_input("🔍 ค้นหารุ่นรถที่ต้องการ...")
    filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df
    for _, row in filtered.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1: st.image(row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/250")
            with col2:
                st.markdown(f"### {row['ยี่ห้อ/รุ่น']} (ID: {row['ID']})")
                s1, s2, s3, s4 = st.columns(4)
                s1.write(f"**💰 ขาย:** {row['ราคาขาย']:,.0f}")
                s2.write(f"**💵 ทุน:** {row['ต้นทุนซื้อ']:,.0f}")
                s3.write(f"**🛠️ ซ่อม:** {row['ค่าซ่อม']:,.0f}")
                s4.write(f"**📈 ROI:** {row['ROI (%)']:.1f}%")
                st.write(f"**📊 ต้นทุนรวม:** {row['ต้นทุนรวม']:,.0f} ฿")
                st.info(f"📝 {row['หมายเหตุ']}")
            st.markdown("---")

# --- 3. อัปเดตสถานะรถ ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 อัปเดตสถานะและบันทึกการขาย")
    if not df.empty:
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} ({x['สถานะ']})", axis=1).tolist()
        target = st.selectbox("เลือกรถที่ต้องการอัปเดต:", target_list)
        tid = target.split(" | ")[0].split(": ")[1]
        target_row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                status_list = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"]
                # แก้ไขจุดที่สะกดผิด 'สถาน e' เป็น 'สถานะ'
                current_idx = status_list.index(target_row['สถานะ']) if target_row['สถานะ'] in status_list else 0
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", status_list, index=current_idx)
                new_sell_price = st.number_input("ราคาขายจริง", value=float(target_row['ราคาขาย']))
            with col2:
                new_fix_cost = st.number_input("ค่าซ่อม (รวมทั้งหมด)", value=float(target_row['ค่าซ่อม']))
                new_note = st.text_area("อัปเดตหมายเหตุ", value=str(target_row['หมายเหตุ']))

            if st.form_submit_button("✅ ยืนยันการอัปเดต"):
                total_cost = float(target_row['ต้นทุนซื้อ']) + new_fix_cost
                new_profit = new_sell_price - total_cost if new_status == "ขายแล้ว" else 0
                
                payload = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix_cost,
                    "total_cost": total_cost,
                    "sell": new_sell_price,
                    "profit": new_profit,
                    "note": new_note
                }
                requests.post(SCRIPT_URL, json=payload)
                st.success("อัปเดตข้อมูลสำเร็จ!")
                time.sleep(1)
                st.rerun()
    else:
        st.info("ไม่มีข้อมูลในระบบ")

# --- 4. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 ลงทะเบียนรถใหม่")
    with st.form("add_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("ยี่ห้อ/รุ่น")
            buy = st.number_input("ทุนซื้อ", min_value=0)
            fix = st.number_input("ค่าซ่อม", min_value=0)
        with c2:
            status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
            grade = st.select_slider("เกรด", options=["C", "B", "B+", "A", "A+"])
        with c3:
            img = st.text_input("ลิงก์รูปภาพ")
            note = st.text_area("หมายเหตุ")
            
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total = buy + fix
            profit = sell - total if sell > 0 else 0
            new_row = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d %H:%M"), img, note, grade]
            requests.post(SCRIPT_URL, json=new_row)
            st.balloons()
            time.sleep(1)
            st.rerun()

# --- 5. ลบข้อมูล ---
elif menu == "🗑️ ล้างฐานข้อมูล":
    st.title("🗑️ Database Management")
    if not df.empty:
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        target = st.selectbox("เลือกข้อมูลที่ต้องการลบ:", target_list)
        confirm = st.checkbox("ยืนยันว่าต้องการลบข้อมูลนี้จริงๆ")
        if confirm and st.button("🚨 ยืนยันการลบถาวร", type="primary"):
            tid = target.split(" | ")[0].split(": ")[1]
            requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
            st.error("ลบข้อมูลเรียบร้อยแล้ว")
            time.sleep(1)
            st.rerun()
