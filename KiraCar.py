import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- CONFIG ---
# อัปเดต URL ใหม่ที่คุณให้มาล่าสุด
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwF29emS2iWI9Z0hncYaCRe5hQn8RUw2U1mwzfPL4dUzDoH-k78_8SfDTukm9QIDoT7IQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
# ใส่พารามิเตอร์ t เพื่อป้องกัน Cache ของ Google Sheets
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Enterprise AI", layout="wide", page_icon="🚀")

# --- CSS Design ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #1a1c23; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=10)
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        # ทำความสะอาดข้อมูลตัวเลข
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ต้นทุนรวม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0)
        return data
    except:
        return pd.DataFrame()

df = load_full_data()

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar BI")
menu = st.sidebar.radio("ระบบบริหารจัดการ", ["📊 แผงควบคุม BI", "🔍 คลังรถยนต์", "📥 ลงทะเบียนรถเข้า", "🗑️ จัดการฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "📊 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    
    if not df.empty:
        # สรุปตัวเลขสำคัญ
        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f} ฿")
        cols[1].metric("📦 มูลค่าสต็อก (ทุน)", f"{df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum():,.0f} ฿")
        cols[2].metric("⏱️ อายุสต็อกเฉลี่ย", f"{df['อายุสต็อก'].mean():.1f} วัน")
        cols[3].metric("🚗 รถทั้งหมด", f"{len(df)} คัน")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 สัดส่วนกำไรตามเกรดรถ")
            if 'เกรดรถ' in df.columns:
                fig = px.pie(df[df['กำไรสุทธิ']>0], values='กำไรสุทธิ', names='เกรดรถ', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("📊 สถานะรถในคลัง")
            fig_status = px.bar(df['สถานะ'].value_counts(), color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig_status, use_container_width=True)

# --- 2. คลังรถยนต์ ---
elif menu == "🔍 คลังรถยนต์":
    st.title("🔍 ค้นหาและวิเคราะห์สต็อก")
    search = st.text_input("พิมพ์รุ่นรถที่ต้องการค้นหา...")
    filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df
    
    for _, row in filtered.iterrows():
        with st.expander(f"ID: {row['ID']} | {row['ยี่ห้อ/รุ่น']} | {row['สถานะ']}"):
            col1, col2 = st.columns([1, 2])
            with col1:
                img_url = row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/300x200"
                st.image(img_url)
            with col2:
                st.write(f"**ต้นทุนรวม (F):** {row['ต้นทุนรวม']:,.0f} ฿")
                st.write(f"**ราคาขาย:** {row['ราคาขาย']:,.0f} ฿")
                st.write(f"**กำไรคาดการณ์:** {row['กำไรสุทธิ']:,.0f} ฿")
                st.write(f"**หมายเหตุ:** {row['หมายเหตุ']}")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 ลงทะเบียนรถเข้า":
    st.title("📥 บันทึกรถยนต์ใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ / รุ่น")
        c1, c2 = st.columns(2)
        with c1:
            buy = st.number_input("ราคาทุนซื้อ (D)", min_value=0)
            fix = st.number_input("ค่าซ่อม (E)", min_value=0)
        with c2:
            sell = st.number_input("ราคาขายเป้าหมาย (G)", min_value=0)
            grade = st.selectbox("เกรดสภาพรถ (L)", ["A+", "A", "B+", "B", "C"])
        
        img = st.text_input("ลิงก์รูปภาพ (J)")
        note = st.text_area("หมายเหตุ (K)")

        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total_cost = buy + fix
            profit = sell - total_cost if sell > 0 else 0
            
            # เรียงลำดับ A-L เพื่อส่งไปที่ Apps Script
            new_car = [
                len(df)+1, name, "กำลังซ่อม", buy, fix, total_cost, 
                sell, profit, datetime.now().strftime("%Y-%m-%d"), 
                img, note, grade
            ]
            
            res = requests.post(SCRIPT_URL, json=new_car)
            if res.status_code == 200:
                st.success(f"บันทึก {name} เรียบร้อย! ทุนรวม {total_cost:,.0f} ฿")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

# --- 4. จัดการฐานข้อมูล (ฉบับเน้นความปลอดภัย) ---
elif menu == "🗑️ จัดการฐานข้อมูล":
    st.title("🗑️ ระบบลบข้อมูลรถยนต์")
    st.warning("คำเตือน: การลบข้อมูลจะเป็นการลบถาวรจาก Google Sheets ไม่สามารถเรียกคืนได้")
    
    if not df.empty:
        # 1. เลือกรถที่ต้องการลบ
        target_options = df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']} (ทุน: {x['ต้นทุนรวม']:,.0f} ฿)", axis=1).tolist()
        target = st.selectbox("เลือกรถที่ต้องการลบออกจากฐานข้อมูล:", target_options)
        
        # ดึง ID ออกมา
        tid = target.split(" | ")[0]
        selected_row = df[df['ID'].astype(str) == tid].iloc[0]
        
        # 2. แสดงรายละเอียดรถที่จะลบเพื่อความมั่นใจ
        st.error(f"⚠️ คุณกำลังจะลบ: {selected_row['ยี่ห้อ/รุ่น']}")
        st.write(f"ID: {tid} | สถานะ: {selected_row['สถานะ']} | ทุนซื้อ: {selected_row['ต้นทุนซื้อ']:,.0f} ฿")
        
        st.markdown("---")
        
        # 3. ขั้นตอนการยืนยัน (Double Verification)
        st.subheader("ยืนยันการทำรายการ")
        confirm_check = st.checkbox(f"ฉันยืนยันว่าต้องการลบข้อมูลรถ ID {tid} นี้ออกจากระบบจริงๆ")
        
        # ปุ่มลบจะขึ้นมาให้กด "ก็ต่อเมื่อ" ติ๊กถูกที่ Checkbox เท่านั้น
        if confirm_check:
            if st.button("🚨 ยืนยันการลบถาวร", type="primary", use_container_width=True):
                with st.spinner("กำลังลบข้อมูลจาก Google Sheets..."):
                    try:
                        res = requests.post(SCRIPT_URL, json={"action": "delete", "id": tid}, timeout=10)
                        if res.status_code == 200:
                            st.success(f"ลบข้อมูล ID {tid} สำเร็จเรียบร้อยแล้ว!")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("เกิดข้อผิดพลาดจากเซิร์ฟเวอร์ ไม่สามารถลบได้")
                    except:
                        st.error("การเชื่อมต่อล้มเหลว")
        else:
            st.info("💡 กรุณาติ๊กถูกที่ช่อง 'ฉันยืนยัน...' ด้านบนเพื่อปลดล็อกปุ่มลบ")
            
    else:
        st.info("ไม่มีข้อมูลในระบบให้ลบ")
