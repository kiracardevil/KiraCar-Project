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

# --- LOAD DATA (ปรับปรุงให้ปลอดภัยขึ้น) ---
@st.cache_data(ttl=10) # เพิ่มเวลา Cache เป็น 10 วินาทีเพื่อลดการดึงข้อมูลซ้ำซ้อน
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        if data.empty:
            return pd.DataFrame()
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['ต้นทุนซื้อ'] = pd.to_numeric(data['ต้นทุนซื้อ'], errors='coerce').fillna(0)
        data['ค่าซ่อม'] = pd.to_numeric(data['ค่าซ่อม'], errors='coerce').fillna(0)
        data['ราคาขาย'] = pd.to_numeric(data['ราคาขาย'], errors='coerce').fillna(0)
        data['กำไรสุทธิ'] = pd.to_numeric(data['กำไรสุทธิ'], errors='coerce').fillna(0)
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0)
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_full_data()

# --- SIDEBAR ---
st.sidebar.title("🚀 KiraCar Enterprise")
menu = st.sidebar.selectbox("เมนูบริหารจัดการ", ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์รถ", "🔄 อัปเดตสถานะรถ", "📥 บันทึกรถเข้า", "🗑️ ล้างฐานข้อมูล"])

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
        with c2:
            st.subheader("🔥 Inventory Velocity")
            if not sold_df.empty:
                brand_speed = sold_df.groupby('ยี่ห้อ/รุ่น')['อายุสต็อก'].mean().sort_values().reset_index()
                st.plotly_chart(px.bar(brand_speed.head(5), x='อายุสต็อก', y='ยี่ห้อ/รุ่น', orientation='h'), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลเพื่อแสดงผล Dashboard")

# --- 2. ค้นหา & วิเคราะห์รถ ---
elif menu == "🔍 ค้นหา & วิเคราะห์รถ":
    st.title("🔍 ค้นหาและประเมินราคารถ")
    search = st.text_input("ค้นหารุ่นรถ...")
    if not df.empty:
        filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df
        for _, row in filtered.iterrows():
            with st.expander(f"🚗 {row['ยี่ห้อ/รุ่น']} (ID: {row['ID']}) - {row['สถานะ']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/250")
                with col2:
                    st.write(f"**💰 ขาย:** {row['ราคาขาย']:,.0f} | **💵 ทุนซื้อ:** {row['ต้นทุนซื้อ']:,.0f}")
                    st.write(f"**🛠️ ค่าซ่อม:** {row['ค่าซ่อม']:,.0f} | **📊 ทุนรวม:** {row['ต้นทุนรวม']:,.0f}")
                    st.write(f"**📈 กำไร:** {row['กำไรสุทธิ']:,.0f} ({row['ROI (%)']:.1f}%)")
                    st.info(f"📝 {row['หมายเหตุ']}")

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
                st.success("อัปเดตเรียบร้อย! กำลังโหลดข้อมูลใหม่...")
                time.sleep(1)
                st.rerun()
    else:
        st.info("ไม่มีข้อมูลรถในระบบ")

# --- 4. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 บันทึกรถเข้า")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("ยี่ห้อ/รุ่น")
        buy = c1.number_input("ทุนซื้อ", min_value=0)
        fix = c1.number_input("ค่าซ่อมเริ่มต้น", min_value=0)
        sell = c2.number_input("ราคาขายตั้งเป้า", min_value=0)
        status = c2.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        grade = c2.select_slider("เกรด", options=["C", "B", "B+", "A", "A+"])
        img = st.text_input("URL รูปภาพ")
        note = st.text_area("หมายเหตุ")
        
        if st.form_submit_button("🚀 บันทึก"):
            total = buy + fix
            profit = sell - total
            data = [len(df)+1, name, status, buy, fix, total, sell, profit, datetime.now().strftime("%Y-%m-%d %H:%M"), img, note, grade]
            requests.post(SCRIPT_URL, json=data)
            st.success("บันทึกสำเร็จ!")
            time.sleep(1)
            st.rerun()

# --- 5. ลบข้อมูล ---
elif menu == "🗑️ ล้างฐานข้อมูล":
    st.title("🗑️ ลบข้อมูล")
    if not df.empty:
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        target = st.selectbox("เลือกรายการที่จะลบ:", target_list)
        if st.checkbox("ยืนยันการลบ") and st.button("🚨 ลบถาวร"):
            tid = target.split(" | ")[0].split(": ")[1]
            requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
            st.rerun()
