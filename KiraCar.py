import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyaLT8rknu6I3ChgQTxfikMEnPn69yBZOcuM_tLn8ggN01uTKuD7UB-XwqUxdQ15-miWQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Hyper Pro", layout="wide", page_icon="⚡")

# --- LOAD & ENHANCE DATA ---
@st.cache_data(ttl=5)
def load_enhanced_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).fillna(0)
        # คำนวณอายุสต็อก (กี่วันที่จอดอยู่)
        data['อายุสต็อก (วัน)'] = (datetime.now() - data['วันที่บันทึก']).dt.days
        return data
    except:
        return pd.DataFrame()

df = load_enhanced_data()

# --- SIDEBAR NAV ---
st.sidebar.markdown("# ⚡ KiraCar Hyper")
menu = st.sidebar.selectbox("เมนูวิเคราะห์", ["📊 Dashboard อัจฉริยะ", "🚘 คลังรถ & AI Pricing", "➕ บันทึกรับรถ", "🗑️ ลบข้อมูล"])

# --- 1. SMART DASHBOARD ---
if menu == "📊 Dashboard อัจฉริยะ":
    st.title("📊 การวิเคราะห์ธุรกิจขั้นสูง")
    
    # KPIs แถวบน
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("💰 กำไรสุทธิรวม", f"{df['กำไรสุทธิ'].sum():,.0f} ฿", delta=f"{len(df)} คัน")
    with k2:
        margin = (df['กำไรสุทธิ'].sum() / df['ราคาขาย'].sum() * 100) if df['ราคาขาย'].sum() > 0 else 0
        st.metric("📉 Margin กำไรภาพรวม", f"{margin:.1f}%")
    with k3:
        dead_stock = len(df[(df['สถานะ'] != 'ขายแล้ว') & (df['อายุสต็อก (วัน)'] > 30)])
        st.metric("⚠️ รถจอดนาน (>30 วัน)", f"{dead_stock} คัน", delta_color="inverse")
    with k4:
        avg_fix = df['ค่าซ่อม'].mean()
        st.metric("🛠️ ค่าซ่อมเฉลี่ย/คัน", f"{avg_fix:,.0f} ฿")

    st.markdown("---")

    # กราฟขั้นเทพ
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📈 เปรียบเทียบ ทุนซื้อ VS ค่าซ่อม (แยกตามรุ่น)")
        fig_cost = px.bar(df.head(10), x='ยี่ห้อ/รุ่น', y=['ต้นทุนซื้อ', 'ค่าซ่อม'], 
                          title="โครงสร้างต้นทุนรถ 10 คันล่าสุด", barmode='stack')
        st.plotly_chart(fig_cost, use_container_width=True)
    with c2:
        st.subheader("🎯 สัดส่วนสถานะรถ")
        fig_donut = go.Figure(data=[go.Pie(labels=df['สถานะ'], values=[1]*len(df), hole=.5)])
        fig_donut.update_layout(showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)

# --- 2. INVENTORY & AI PRICING ---
elif menu == "🚘 คลังรถ & AI Pricing":
    st.title("🚘 จัดการคลังและ AI ตั้งราคา")
    
    # ตัวกรองอัจฉริยะ
    f1, f2 = st.columns(2)
    with f1:
        status_filter = st.multiselect("กรองสถานะ", df['สถานะ'].unique(), default=df['สถานะ'].unique())
    with f2:
        search = st.text_input("🔍 ค้นหารุ่นรถ")

    display_df = df[df['สถานะ'].isin(status_filter)]
    if search:
        display_df = display_df[display_df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)]

    # แสดงผลแบบ Card พร้อม AI Suggestion
    for _, row in display_df.iterrows():
        color = "red" if row['อายุสต็อก (วัน)'] > 30 and row['สถานะ'] != 'ขายแล้ว' else "black"
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                img = row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/200"
                st.image(img)
            with col2:
                st.markdown(f"### <span style='color:{color}'>{row['ยี่ห้อ/รุ่น']}</span>", unsafe_allow_html=True)
                st.write(f"**ต้นทุนรวม:** {row['ต้นทุนรวม']:,.0f} ฿ | **อายุสต็อก:** {row['อายุสต็อก (วัน)']} วัน")
                if row['สถานะ'] != 'ขายแล้ว':
                    # AI Suggestion
                    suggested_price = row['ต้นทุนรวม'] * 1.20 # สมมติเอากำไร 20%
                    st.info(f"💡 AI แนะนำราคาขาย (Margin 20%): **{suggested_price:,.0f} ฿**")
            with col3:
                st.write(f"**สถานะ:** {row['สถานะ']}")
                st.write(f"**ROI:** {row['ROI (%)']:.1f}%")
                if st.button("ดูรายละเอียด/หมายเหตุ", key=row['ID']):
                    st.write(f"📝 {row['หมายเหตุ']}")
            st.markdown("---")

# --- 3. บันทึกรับรถ (เพิ่มช่องหมายเหตุ) ---
elif menu == "➕ บันทึกรับรถ":
    st.title("➕ ลงทะเบียนรถเข้าคลัง")
    with st.form("pro_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("ยี่ห้อ / รุ่น")
            buy = st.number_input("ทุนซื้อ", min_value=0)
            fix = st.number_input("ค่าซ่อม", min_value=0)
        with c2:
            status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell = st.number_input("ราคาขาย", min_value=0)
            img = st.text_input("ลิงก์รูปภาพ")
        
        note = st.text_area("หมายเหตุ (เช่น ตำหนิ, ประวัติการซ่อม)")
        
        if st.form_submit_button("🚀 บันทึกเข้าระบบ Hyper"):
            profit = sell - (buy + fix) if sell > 0 else 0
            new_row = [len(df)+1, name, status, buy, fix, sell, profit, 
                       datetime.now().strftime("%Y-%m-%d %H:%M"), img, note]
            requests.post(SCRIPT_URL, json=new_row)
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# --- 4. ลบข้อมูล ---
elif menu == "🗑️ ลบข้อมูล":
    st.title("🗑️ จัดการฐานข้อมูล")
    options = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
    target = st.selectbox("เลือกรายการที่จะลบ", options)
    if st.button("🚨 ยืนยันการลบ (ถาวร)"):
        target_id = target.split(" | ")[0].split(": ")[1]
        requests.post(SCRIPT_URL, json={"action": "delete", "id": target_id})
        st.error(f"ลบ ID {target_id} สำเร็จ")
        st.rerun()
