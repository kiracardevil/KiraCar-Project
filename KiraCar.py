import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx_UJcQh2yA5mj8g38RntjhcOakHf5ZlYtVbI-t6p3n79uTHQIuHodJdy9l56HCjThxAw/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"

st.set_page_config(page_title="KiraCar Enterprise AI", layout="wide", page_icon="🚀")

# --- CSS Design (High Contrast Sidebar) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    [data-testid="stSidebar"] { background-color: #1a1c23; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label {
        color: #FFFFFF !important; font-weight: 500;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        color: #FFFFFF !important; background-color: rgba(255, 255, 255, 0.05);
        margin-bottom: 5px; padding: 8px 15px; border-radius: 8px;
    }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=10)
def load_full_data():
    try:
        data = pd.read_csv(SHEET_URL)
        num_cols = ['ต้นทุนซื้อ', 'ค่าซ่อม', 'ต้นทุนรวม', 'ราคาขาย', 'กำไรสุทธิ']
        for col in num_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
        data['วันที่บันทึก'] = pd.to_datetime(data['วันที่บันทึก'], errors='coerce')
        data['อายุสต็อก'] = (datetime.now() - data['วันที่บันทึก']).dt.days.fillna(0).astype(int)
        return data
    except:
        return pd.DataFrame()

df = load_full_data()
GRADE_OPTIONS = ["A+", "A", "B+", "B", "C+", "C", "D"]

# --- FUNCTIONS (Global Color Logic) ---
def apply_color_logic(row):
    # สถานะ: พร้อมขาย(เขียว), กำลังซ่อม(แดง), ขายแล้ว(ฟ้า)
    if row['สถานะ'] == 'กำลังซ่อม':
        status_style = 'color: #dc3545; font-weight: bold'
    elif row['สถานะ'] == 'พร้อมขาย':
        status_style = 'color: #28a745; font-weight: bold'
    else:
        status_style = 'color: #007bff; font-weight: bold'
    
    styles = [''] * len(row)
    styles[3] = status_style                         # คอลัมน์สถานะ
    styles[5] = 'color: #28a745; font-weight: bold'  # ราคาขาย (เขียว)
    styles[6] = 'color: #dc3545;'                    # หมายเหตุ (แดง)
    return styles

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar BI")
menu = st.sidebar.radio("ระบบบริหารจัดการ", 
                        ["📊 แผงควบคุม BI", "🔍 คลังรถยนต์", "📥 ลงทะเบียนรถเข้า", "🔄 อัปเดตสถานะ/ค่าซ่อม", "📋 รายงานและสรุปผล", "🗑️ จัดการฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "📊 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    if not df.empty:
        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{int(df['กำไรสุทธิ'].sum()):,} ฿")
        cols[1].metric("📦 มูลค่าสต็อก (ทุน)", f"{int(df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()):,} ฿")
        cols[2].metric("⏱️ อายุสต็อกเฉลี่ย", f"{df['อายุสต็อก'].mean():.1f} วัน")
        cols[3].metric("🚗 รถทั้งหมด", f"{len(df)} คัน")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 สัดส่วนกำไรตามเกรดรถ")
            plot_df = df[df['กำไรสุทธิ']>0]
            if not plot_df.empty:
                fig = px.pie(plot_df, values='กำไรสุทธิ', names='เกรดรถ', hole=0.4, category_orders={"เกรดรถ": GRADE_OPTIONS})
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("📊 สถานะรถในคลัง")
            fig_status = px.bar(df['สถานะ'].value_counts())
            st.plotly_chart(fig_status, use_container_width=True)

# --- 2. คลังรถยนต์ ---
elif menu == "🔍 คลังรถยนต์":
    st.title("🔍 ค้นหาและวิเคราะห์สต็อก")
    search = st.text_input("พิมพ์รุ่นรถที่ต้องการค้นหา...")
    filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df
    
    for _, row in filtered.iterrows():
        # กำหนดสีตามสถานะสำหรับหัวข้อ Expander
        status_label = row['สถานะ']
        if status_label == "พร้อมขาย":
            display_status = f"🟢 {status_label}"
        elif status_label == "กำลังซ่อม":
            display_status = f"🔴 {status_label}"
        else: # ขายแล้ว
            display_status = f"🔵 {status_label}"

        # แสดงผลกล่องข้อมูลรถ
        with st.expander(f"ID: {row['ID']} | {row['ยี่ห้อ/รุ่น']} | เกรด: {row['เกรดรถ']} | {display_status}"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/300x200")
            with col2:
                # ใช้ markdown เพื่อใส่สีตัวอักษรในเนื้อหา
                st.markdown(f"**สถานะ:** <span style='color:{'green' if status_label=='พร้อมขาย' else 'red' if status_label=='กำลังซ่อม' else 'blue'}; font-weight:bold;'>{status_label}</span>", unsafe_allow_html=True)
                st.write(f"**ต้นทุนรวม:** {int(row['ต้นทุนรวม']):,} ฿")
                st.markdown(f"**ราคาขาย:** <span style='color:green; font-weight:bold;'>{int(row['ราคาขาย']):,} ฿</span>", unsafe_allow_html=True)
                st.write(f"**กำไร:** {int(row['กำไรสุทธิ']):,} ฿")
                st.markdown(f"**หมายเหตุ:** <span style='color:red;'>{row['หมายเหตุ']}</span>", unsafe_allow_html=True)
                
# --- 3. ลงทะเบียนรถเข้า ---
elif menu == "📥 ลงทะเบียนรถเข้า":
    st.title("📥 บันทึกรถยนต์ใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ / รุ่น")
        c1, c2 = st.columns(2)
        with c1:
            buy = st.number_input("ราคาทุนซื้อ (D)", min_value=0, step=1)
            fix = st.number_input("ค่าซ่อม (E)", min_value=0, step=1)
        with c2:
            sell = st.number_input("ราคาขายเป้าหมาย (G)", min_value=0, step=1)
            grade = st.selectbox("เกรดสภาพรถ (L)", GRADE_OPTIONS)
        img = st.text_input("ลิงก์รูปภาพ (J)")
        note = st.text_area("หมายเหตุ (K)")
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total_cost = int(buy + fix)
            profit = int(sell - total_cost) if sell > 0 else 0
            new_car = [int(len(df)+1), name, "กำลังซ่อม", int(buy), int(fix), total_cost, int(sell), profit, datetime.now().strftime("%Y-%m-%d"), img, note, grade]
            requests.post(SCRIPT_URL, json=new_car)
            st.success(f"บันทึกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()

# --- 4. อัปเดตสถานะ/ค่าซ่อม ---
elif menu == "🔄 อัปเดตสถานะ/ค่าซ่อม":
    st.title("🔄 อัปเดตสถานะและเกรดรถ")
    if not df.empty:
        # ล็อกชื่อคอลัมน์เกรดรถให้ชัดเจน
        target_col = 'เกรดรถ'
        
# สร้างรายชื่อรถให้เลือก: เพิ่มการโชว์ต้นทุนรวม (ทุนซื้อ + ค่าซ่อม)
        car_list = df.apply(
            lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']} | ต้นทุนรวม: {int(x['ต้นทุนรวม']):,} ฿ (เกรดเดิม: {x[target_col]})", 
            axis=1
        ).tolist()
        
        target = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_list)
        tid = target.split(" | ")[0]
        
        # ดึงข้อมูลของรถคันที่เลือกมาแสดงในฟอร์ม
        row = df[df['ID'].astype(str) == tid].iloc[0]
        
        with st.form("update_form"):
            c1, c2 = st.columns(2)
            with c1:
                # อัปเดตสถานะ
                current_status = row['สถานะ']
                status_index = ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(current_status) if current_status in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], index=status_index)
                
                new_sell = st.number_input("ปรับราคาขาย (G)", value=int(row['ราคาขาย']), step=1)
                # ใส่ไว้ในฝั่ง c1 หรือใต้ช่อง new_sell
current_profit = new_sell - (row['ต้นทุนซื้อ'] + new_fix)
st.caption(f"💡 กำไรคาดการณ์: {int(current_profit):,} ฿")

                # --- จุดที่แก้ไข: อัปเดตเกรดรถ ---
                current_grade = str(row[target_col]).strip() # ล้างช่องว่างออก
                # หาตำแหน่ง Index ของเกรดปัจจุบันในลิสต์ GRADE_OPTIONS
                try:
                    grade_index = GRADE_OPTIONS.index(current_grade)
                except ValueError:
                    grade_index = 1 # ถ้าหาไม่เจอให้ไปที่เกรด A เป็นค่าเริ่มต้น
                
                new_grade = st.selectbox("แก้ไขเกรดรถ (L):", GRADE_OPTIONS, index=grade_index)

            with c2:
                new_fix = st.number_input("ยอดค่าซ่อมรวมใหม่ (E)", value=int(row['ค่าซ่อม']), step=1)
                new_note = st.text_area("บันทึกเพิ่มเติม (K)", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ ยืนยันการอัปเดต"):
                # คำนวณต้นทุนและกำไรใหม่ก่อนส่ง
                total_f = int(row['ต้นทุนซื้อ'] + new_fix)
                profit_h = int(new_sell - total_f) if new_sell > 0 else 0
                
                # ส่งข้อมูลไปที่ Google Apps Script
                payload = {
                    "action": "update", 
                    "id": str(tid), 
                    "status": new_status, 
                    "fix": int(new_fix), 
                    "total_cost": total_f, 
                    "sell": int(new_sell), 
                    "profit": profit_h, 
                    "note": new_note, 
                    "grade": str(new_grade) # ส่งเกรดใหม่ไปที่คอลัมน์ L
                }
                
                try:
                    response = requests.post(SCRIPT_URL, json=payload)
                    if response.status_code == 200:
                        st.success(f"อัปเดต ID {tid} เรียบร้อยแล้ว (เกรดใหม่: {new_grade})")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 5. รายงานและสรุปผล ---
elif menu == "📋 รายงานและสรุปผล":
    st.title("📋 รายงานและสรุปผลธุรกิจ")
    tab1, tab2 = st.tabs(["📄 สรุปรายการรถ (Print)", "📈 สรุปยอดขายประจำเดือน"])
    
    with tab1:
        st.subheader("🖨️ รายงานสต็อกรถยนต์")
        report_type = st.radio("เลือกดูรายการ:", ["เฉพาะรถพร้อมขาย", "รถทั้งหมด"], horizontal=True)
        print_df = df[df['สถานะ'] == 'พร้อมขาย'] if report_type == "เฉพาะรถพร้อมขาย" else df

        if not print_df.empty:
            display_df = print_df[['ID', 'ยี่ห้อ/รุ่น', 'เกรดรถ', 'สถานะ', 'ต้นทุนรวม', 'ราคาขาย', 'หมายเหตุ']].copy()
            display_df['ต้นทุนรวม'] = display_df['ต้นทุนรวม'].apply(lambda x: f"{x:,.0f}")
            display_df['ราคาขาย'] = display_df['ราคาขาย'].apply(lambda x: f"{x:,.0f}")
            display_df.index = range(1, len(display_df) + 1)

            # ตารางแบบบีบช่องไฟ และสูงพอสำหรับ 24 คัน
            st.dataframe(
                display_df.style.apply(apply_color_logic, axis=1),
                use_container_width=True,
                height=900, 
                column_config={
                    "ID": st.column_config.Column(width="small"),
                    "ยี่ห้อ/รุ่น": st.column_config.Column(width="medium"),
                    "เกรดรถ": st.column_config.Column(width="small"),
                    "สถานะ": st.column_config.Column(width="small"),
                    "ต้นทุนรวม": st.column_config.Column(width="small"),
                    "ราคาขาย": st.column_config.Column(width="small"),
                    "หมายเหตุ": st.column_config.Column(width="large"),
                }
            )
            st.download_button("📥 Download Report (CSV)", display_df.to_csv(index=True).encode('utf-8-sig'), "car_report.csv", "text/csv")
        else: st.warning("ไม่มีข้อมูล")

    with tab2:
        st.subheader("📅 สรุปยอดขายรายเดือน")
        sold_df = df[df['สถานะ'] == 'ขายแล้ว'].copy()
        if not sold_df.empty:
            sold_df['เดือนที่ขาย'] = sold_df['วันที่บันทึก'].dt.strftime('%Y-%m')
            month = st.selectbox("เลือกเดือน:", sorted(sold_df['เดือนที่ขาย'].unique(), reverse=True))
            monthly = sold_df[sold_df['เดือนที่ขาย'] == month]
            m1, m2, m3 = st.columns(3)
            m1.metric("🚗 ขายได้", f"{len(monthly)} คัน")
            m2.metric("💰 ยอดขาย", f"{int(monthly['ราคาขาย'].sum()):,} ฿")
            m3.metric("📈 กำไร", f"{int(monthly['กำไรสุทธิ'].sum()):,} ฿")
            
            monthly_display = monthly[['ID', 'ยี่ห้อ/รุ่น', 'เกรดรถ', 'ต้นทุนรวม', 'ราคาขาย', 'กำไรสุทธิ']].copy()
            monthly_display.index = range(1, len(monthly_display) + 1)
            st.table(monthly_display)
        else: st.info("ยังไม่มีรายการที่ขายแล้ว")

# --- 6. จัดการฐานข้อมูล ---
elif menu == "🗑️ จัดการฐานข้อมูล":
    st.title("🗑️ ระบบลบข้อมูล")
    if not df.empty:
        target = st.selectbox("เลือกรถที่ต้องการลบ:", df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1))
        tid = target.split(" | ")[0]
        if st.checkbox(f"ยืนยันลบ ID {tid}"):
            if st.button("🚨 ลบถาวร", type="primary"):
                requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
                st.error("ลบสำเร็จ"); st.cache_data.clear(); time.sleep(1); st.rerun()







