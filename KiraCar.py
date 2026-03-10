import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px  # ตัวทำกราฟ

# --- ตั้งค่าเริ่มต้น ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Management Pro", layout="wide", page_icon="🚗")

# --- ส่วนการดึงข้อมูล ---
@st.cache_data(ttl=5) # เก็บแคชไว้แค่ 5 วินาทีเพื่อให้ข้อมูลสดใหม่
def load_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['กำไรสุทธิ'] = pd.to_numeric(data['กำไรสุทธิ'], errors='coerce').fillna(0)
        return data
    except:
        return pd.DataFrame(columns=["ID", "ยี่ห้อ/รุ่น", "สถานะ", "ต้นทุนซื้อ", "ค่าซ่อม", "ราคาขาย", "กำไรสุทธิ", "วันที่บันทึก"])

df = load_data()

# --- เมนูหลัก ---
st.sidebar.title("🛠 KiraCar Menu")
menu = st.sidebar.selectbox("เลือกฟังก์ชันการใช้งาน", ["📊 Dashboard & ค้นหา", "➕ บันทึกรถเข้าใหม่", "🗑️ ลบข้อมูลรถ"])

# --- 1. หน้า Dashboard & ค้นหา & กราฟ ---
if menu == "📊 Dashboard & ค้นหา":
    st.title("📊 รายงานและคลังรถยนต์")
    
    # สรุปตัวเลขด้านบน
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 กำไรสะสมทั้งหมด", f"{df['กำไรสุทธิ'].sum():,.0f} บาท")
    with col2:
        st.metric("🚘 รถทั้งหมดในระบบ", f"{len(df)} คัน")
    with col3:
        sold_count = len(df[df['สถานะ'] == 'ขายแล้ว'])
        st.metric("✅ ขายออกแล้ว", f"{sold_count} คัน")

    st.markdown("---")

    # ส่วนระบบค้นหา (Search)
    st.subheader("🔍 ค้นหารถยนต์ในคลัง")
    search_query = st.text_input("ค้นหาตามชื่อรุ่น หรือ ยี่ห้อรถ...")
    
    if search_query:
        display_df = df[df['ยี่ห้อ/รุ่น'].str.contains(search_query, case=False, na=False)]
    else:
        display_df = df

    st.dataframe(display_df, use_container_width=True)

    # ส่วนกราฟกำไรรายเดือน
    st.markdown("---")
    st.subheader("📈 วิเคราะห์กำไรรายเดือน")
    if not df.empty:
        # จัดกลุ่มข้อมูลตามเดือน
        df['เดือน-ปี'] = df['วันที่บันทึก'].dt.strftime('%Y-%m')
        monthly_profit = df.groupby('เดือน-ปี')['กำไรสุทธิ'].sum().reset_index()
        
        fig = px.bar(monthly_profit, x='เดือน-ปี', y='กำไรสุทธิ',
                     title="ยอดกำไรสุทธิแยกตามเดือน",
                     labels={'กำไรสุทธิ': 'กำไร (บาท)', 'เดือน-ปี': 'เดือนที่บันทึก'},
                     color='กำไรสุทธิ', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลสำหรับทำกราฟ")

# --- 2. หน้าบันทึกข้อมูล ---
elif menu == "➕ บันทึกรถเข้าใหม่":
    st.title("➕ ลงทะเบียนรถเข้าใหม่")
    with st.form("add_car_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("ยี่ห้อ / รุ่นรถ (เช่น Honda Civic 2020)")
            buy_p = st.number_input("ราคาทุนที่ซื้อมา", min_value=0)
            fix_p = st.number_input("ค่าซ่อมและปรับสภาพ", min_value=0)
        with c2:
            status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell_p = st.number_input("ราคาขาย (ถ้ายังไม่ขายใส่ 0)", min_value=0)
        
        if st.form_submit_button("💾 บันทึกข้อมูล"):
            if name:
                profit = sell_p - (buy_p + fix_p) if sell_p > 0 else 0
                # ข้อมูลที่จะส่ง (Action ปกติ)
                new_row = [len(df)+1, name, status, buy_p, fix_p, sell_p, profit, datetime.now().strftime("%Y-%m-%d %H:%M")]
                requests.post(SCRIPT_URL, json=new_row)
                st.success(f"บันทึก {name} เรียบร้อย!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.warning("กรุณากรอกชื่อรุ่นรถ")

# --- 3. หน้าลบข้อมูล ---
elif menu == "🗑️ ลบข้อมูลรถ":
    st.title("🗑️ จัดการลบข้อมูล")
    st.warning("ระวัง! การลบข้อมูลจะไม่สามารถกู้คืนได้")
    
    if not df.empty:
        # สร้างตัวเลือกจากชื่อรถและ ID
        options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        target = st.selectbox("เลือกรายการรถที่ต้องการลบออกจากระบบ", options)
        target_id = target.split(" | ")[0].
