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

st.set_page_config(page_title="KiraCar Enterprise AI", layout="wide", page_icon="🚀")

# --- CSS เพื่อความสวยงามระดับเทพ ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=5)
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['ต้นทุนรวม'] = data['ต้นทุนซื้อ'] + data['ค่าซ่อม']
        data['ROI (%)'] = (data['กำไรสุทธิ'] / data['ต้นทุนรวม'] * 100).fillna(0)
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days
        return data
    except:
        return pd.DataFrame()

df = load_full_data()

# --- SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/741/741407.png", width=100)
st.sidebar.title("KiraCar Enterprise")
menu = st.sidebar.radio("เมนูบริหารจัดการ", ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์รถ", "📥 บันทึกรถเข้า", "🗑️ ล้างฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "💎 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    
    # KPIs แถวบน
    cols = st.columns(4)
    with cols[0]:
        st.metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f}", "THB")
    with cols[1]:
        avg_turnover = df[df['สถานะ']=='ขายแล้ว']['อายุสต็อก'].mean()
        st.metric("⏱️ ปิดการขายเฉลี่ย", f"{avg_turnover:.1f} วัน")
    with cols[2]:
        total_inv = df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()
        st.metric("📦 มูลค่าสินค้าคงคลัง", f"{total_inv:,.0f}", "THB")
    with cols[3]:
        win_rate = (len(df[df['สถานะ']=='ขายแล้ว']) / len(df) * 100) if len(df)>0 else 0
        st.metric("📈 อัตราการขายออก", f"{win_rate:.1f}%")

    st.markdown("---")
    
    # กราฟวิเคราะห์
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📊 กำไรแยกตามเกรดรถ (A/B/C)")
        if 'เกรดรถ' in df.columns:
            fig_grade = px.sunburst(df, path=['เกรดรถ', 'สถานะ'], values='กำไรสุทธิ', color='เกรดรถ')
            st.plotly_chart(fig_grade, use_container_width=True)
    with c2:
        st.subheader("🔥 Inventory Velocity (ยี่ห้อไหนขายไว)")
        if not df.empty:
            brand_speed = df[df['สถานะ']=='ขายแล้ว'].groupby('ยี่ห้อ/รุ่น')['อายุสต็อก'].mean().sort_values().reset_index()
            fig_speed = px.bar(brand_speed.head(5), x='อายุสต็อก', y='ยี่ห้อ/รุ่น', orientation='h', color='อายุสต็อก')
            st.plotly_chart(fig_speed, use_container_width=True)

# --- 2. ค้นหา & วิเคราะห์รถ ---
elif menu == "🔍 ค้นหา & วิเคราะห์รถ":
    st.title("🔍 ค้นหาและประเมินราคารถ")
    
    # ตัวเลือกจัดเรียง (ความเทพอยู่ตรงนี้)
    sort_by = st.selectbox("จัดเรียงตาม:", ["ล่าสุด", "กำไรสูงสุด", "จอดนานที่สุด", "ต้นทุนต่ำสุด"])
    
    if sort_by == "กำไรสูงสุด": df = df.sort_values('กำไรสุทธิ', ascending=False)
    elif sort_by == "จอดนานที่สุด": df = df.sort_values('อายุสต็อก', ascending=False)
    elif sort_by == "ต้นทุนต่ำสุด": df = df.sort_values('ต้นทุนรวม', ascending=True)

    search = st.text_input("ค้นหารุ่นรถที่ต้องการ...")
    filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df

    for _, row in filtered.iterrows():
        # แสดงผลแบบ High-End Card
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                img = row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/250"
                st.image(img, use_column_width=True)
            with col2:
                # แท็กสถานะ
                st.markdown(f"### {row['ยี่ห้อ/รุ่น']} <span style='font-size:14px; background:#e1f5fe; padding:2px 8px; border-radius:5px;'>ID: {row['ID']}</span>", unsafe_allow_html=True)
                
                sub1, sub2, sub3 = st.columns(3)
                sub1.write(f"**💰 ราคาขาย:** {row['ราคาขาย']:,.0f}")
                sub2.write(f"**🛠 ทุนรวม:** {row['ต้นทุนรวม']:,.0f}")
                sub3.write(f"**📈 ROI:** {row['ROI (%)']:.1f}%")
                
                # แจ้งเตือน AI
                if row['สถานะ'] != 'ขายแล้ว' and row['อายุสต็อก'] > 45:
                    st.error(f"⚠️ คำเตือน: รถคันนี้จอดมา {row['อายุสต็อก']} วันแล้ว (สต็อกเริ่มตาย) แนะนำให้ลดราคา 5% เพื่อระบายออก")
                
                st.info(f"📝 หมายเหตุ: {row['หมายเหตุ']}")
            st.markdown("---")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 ลงทะเบียนรถยนต์เข้าสู่ระบบ AI")
    with st.form("enterprise_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("ยี่ห้อ / รุ่น")
            buy = st.number_input("ราคาทุน", min_value=0)
            fix = st.number_input("ค่าซ่อม", min_value=0)
        with c2:
            status = st.selectbox("สถานะ", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell = st.number_input("ราคาขายตั้งเป้า", min_value=0)
            grade = st.select_slider("เกรดสภาพรถ", options=["C", "B", "B+", "A", "A+"])
        with c3:
            img = st.text_input("ลิงก์รูปภาพ (URL)")
            note = st.text_area("หมายเหตุเชิงลึก")
            
        if st.form_submit_button("🚀 บันทึกข้อมูลระดับ Enterprise"):
            profit = sell - (buy + fix) if sell > 0 else 0
            # ส่งข้อมูล 11 คอลัมน์ (รวม เกรดรถ)
            new_data = [len(df)+1, name, status, buy, fix, sell, profit, 
                        datetime.now().strftime("%Y-%m-%d %H:%M"), img, note, grade]
            requests.post(SCRIPT_URL, json=new_data)
            st.balloons()
            st.success(f"บันทึก {name} เข้าคลังสินค้าเรียบร้อย!")
            time.sleep(1)
            st.rerun()

# --- 4. ลบข้อมูล ---
elif menu == "🗑️ ล้างฐานข้อมูล":
    st.title("🗑️ Database Management")
    target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1).tolist()
    target = st.selectbox("เลือกข้อมูลที่ต้องการลบถาวร", target_list)
    if st.button("🚨 ยืนยันการลบถาวร"):
        tid = target.split(" | ")[0].split(": ")[1]
        requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
        st.error(f"ลบข้อมูล ID {tid} เรียบร้อย")
        time.sleep(1)
        st.rerun()
