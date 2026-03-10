import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- ตั้งค่าเริ่มต้น ---
SCRIPT_URL = "ใส่_WEB_APP_URL_ของคุณ"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Pro", layout="wide", page_icon="🚗")

# ดึงข้อมูล
try:
    df = pd.read_csv(SHEET_URL)
    df['วันที่บันทึก'] = pd.to_datetime(df['วันที่บันทึก'], errors='coerce')
    df['กำไรสุทธิ'] = pd.to_numeric(df['กำไรสุทธิ'], errors='coerce').fillna(0)
except:
    df = pd.DataFrame(columns=["ID", "ยี่ห้อ/รุ่น", "สถานะ", "ต้นทุนซื้อ", "ค่าซ่อม", "ราคาขาย", "กำไรสุทธิ", "วันที่บันทึก"])

st.title("🚗 KiraCar Management System Pro")

menu = st.sidebar.selectbox("เมนู", ["📊 Dashboard & Search", "➕ บันทึกรถเข้าใหม่", "🗑️ ลบข้อมูล"])

# --- 1. Dashboard & Search & Graph ---
if menu == "📊 Dashboard & Search":
    # ส่วนของตัวเลขสรุป
    c1, c2 = st.columns(2)
    with c1:
        st.metric("กำไรสะสมทั้งหมด", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
    with c2:
        st.metric("จำนวนรถในคลัง", f"{len(df)} คัน")

    # ส่วนค้นหา (Search)
    st.markdown("### 🔍 ค้นหารถยนต์")
    search_query = st.text_input("พิมพ์ ยี่ห้อ หรือ รุ่นรถ ที่ต้องการหา...")
    
    filtered_df = df.copy()
    if search_query:
        filtered_df = df[df['ยี่ห้อ/รุ่น'].str.contains(search_query, case=False, na=False)]
    
    st.dataframe(filtered_df, use_container_width=True)

    # ส่วนกราฟกำไรรายเดือน
    st.markdown("### 📈 กราฟกำไรรายเดือน")
    if not df.empty:
        df['Month-Year'] = df['วันที่บันทึก'].dt.strftime('%Y-%m')
        monthly_profit = df.groupby('Month-Year')['กำไรสุทธิ'].sum().reset_index()
        fig = px.bar(monthly_profit, x='Month-Year', y='กำไรสุทธิ', 
                     title="กำไรสุทธิแยกตามเดือน",
                     labels={'กำไรสุทธิ': 'กำไร (บาท)', 'Month-Year': 'เดือน'},
                     color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)

# --- 2. บันทึกข้อมูล (แบบเดิม) ---
elif menu == "➕ บันทึกรถเข้าใหม่":
    with st.form("add_car"):
        name = st.text_input("ยี่ห้อ / รุ่นรถ")
        buy = st.number_input("ทุนซื้อ", min_value=0)
        fix = st.number_input("ค่าซ่อม", min_value=0)
        sell = st.number_input("ราคาขาย", min_value=0)
        stat = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
        
        if st.form_submit_button("💾 บันทึก"):
            profit = sell - (buy + fix) if sell > 0 else 0
            new_data = [len(df)+1, name, stat, buy, fix, sell, profit, datetime.now().strftime("%Y-%m-%d %H:%M")]
            res = requests.post(SCRIPT_URL, json=new_data)
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# --- 3. ระบบลบข้อมูล (Delete) ---
elif menu == "🗑️ ลบข้อมูล":
    st.subheader("เลือกรายการที่ต้องการลบ")
    if not df.empty:
        # สร้างรายการให้เลือกเพื่อลบ
        list_to_delete = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
        selected_item = st.selectbox("เลือกรายการ", list_to_delete)
        selected_id = selected_item.split(" | ")[0].split(": ")[1]

        if st.button("🚨 ยืนยันการลบข้อมูล"):
            delete_payload = {"action": "delete", "id": selected_id}
            res = requests.post(SCRIPT_URL, json=delete_payload)
            if "Success" in res.text:
                st.warning(f"ลบข้อมูล ID {selected_id} เรียบร้อยแล้ว")
                time.sleep(1)
                st.rerun()
    else:
        st.info("ไม่มีข้อมูลให้ลบ")
