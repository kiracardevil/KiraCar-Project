import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# --- CONFIG ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwF29emS2iWI9Z0hncYaCRe5hQn8RUw2U1mwzfPL4dUzDoH-k78_8SfDTukm9QIDoT7IQ/exec"
SHEET_ID = "1xQqrXTZ5lDCPuRcNfYDUjLqmZ3PVNtbW4s9Ot1ejHYo"
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

# รายชื่อเกรดที่กำหนดใหม่
GRADE_OPTIONS = ["A+", "A", "B+", "B", "C+", "C", "D"]

# --- SIDEBAR ---
st.sidebar.title("💎 KiraCar BI")
menu = st.sidebar.radio("ระบบบริหารจัดการ", 
                        ["📊 แผงควบคุม BI", "🔍 คลังรถยนต์", "📥 ลงทะเบียนรถเข้า", "🔄 อัปเดตสถานะ/ค่าซ่อม", "🗑️ จัดการฐานข้อมูล"])

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
            st.subheader("📈 สัดส่วนกำไรตามเกรดรถ (A+ ถึง D)")
            plot_df = df[df['กำไรสุทธิ']>0]
            if not plot_df.empty:
                fig = px.pie(plot_df, values='กำไรสุทธิ', names='เกรดรถ', hole=0.4,
                             category_orders={"เกรดรถ": GRADE_OPTIONS})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ยังไม่มีข้อมูลกำไร")
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
        with st.expander(f"ID: {row['ID']} | {row['ยี่ห้อ/รุ่น']} | เกรด: {row['เกรดรถ']} | {row['สถานะ']}"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/300x200")
            with col2:
                st.write(f"**ต้นทุนรวม (F):** {int(row['ต้นทุนรวม']):,} ฿")
                st.write(f"**ราคาขาย:** {int(row['ราคาขาย']):,} ฿")
                st.write(f"**กำไร:** {int(row['กำไรสุทธิ']):,} ฿")
                st.write(f"**หมายเหตุ:** {row['หมายเหตุ']}")

# --- 3. บันทึกรถเข้า ---
elif menu == "📥 ลงทะเบียนรถเข้า":
    st.title("📥 บันทึกรถยนต์ใหม่")
    with st.form("add_form"):
        name = st.text_input("ยี่ห้อ / รุ่น")
        c1, c2 = st.columns(2)
        with c1:
            buy = st.number_input("ราคาทุนซื้อ (D)", min_value=0, step=1, format="%d")
            fix = st.number_input("ค่าซ่อม (E)", min_value=0, step=1, format="%d")
        with c2:
            sell = st.number_input("ราคาขายเป้าหมาย (G)", min_value=0, step=1, format="%d")
            grade = st.selectbox("เกรดสภาพรถ (L)", GRADE_OPTIONS) # อัปเดตถึงเกรด D
        img = st.text_input("ลิงก์รูปภาพ (J)")
        note = st.text_area("หมายเหตุ (K)")
        
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total_cost = int(buy + fix)
            profit = int(sell - total_cost) if sell > 0 else 0
            new_car = [int(len(df)+1), name, "กำลังซ่อม", int(buy), int(fix), total_cost, int(sell), profit, datetime.now().strftime("%Y-%m-%d"), img, note, grade]
            requests.post(SCRIPT_URL, json=new_car)
            st.success(f"บันทึกสำเร็จ! เกรดรถ: {grade}"); st.cache_data.clear(); time.sleep(1); st.rerun()

# --- 4. อัปเดตสถานะ/ค่าซ่อม (แก้ไขให้บันทึกเกรดลงฐานข้อมูลได้จริง) ---
elif menu == "🔄 อัปเดตสถานะ/ค่าซ่อม":
    st.title("🔄 อัปเดตสถานะและเกรดรถ")
    if not df.empty:
        # ดึงชื่อคอลัมน์ให้ชัวร์ (บางทีใน df อาจเป็น 'เกรดรถ' หรือ 'Grade')
        grade_col = 'เกรดรถ' if 'เกรดรถ' in df.columns else df.columns[-1] 
        
        car_list = df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']} (เกรดปัจจุบัน: {x[grade_col]})", axis=1).tolist()
        target = st.selectbox("เลือกรถที่ต้องการอัปเดต:", car_list)
        tid = target.split(" | ")[0]
        row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], 
                                          index=["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(row['สถานะ']) if row['สถานะ'] in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0)
                new_sell = st.number_input("ปรับราคาขาย (G)", value=int(row['ราคาขาย']), step=1, format="%d")
                
                # ดึงเกรดเดิมมาตั้งต้น ถ้าหาไม่เจอให้เริ่มที่ C
                current_grade_val = str(row[grade_col]) if grade_col in row else "C"
                new_grade = st.selectbox("แก้ไขเกรดรถ (L):", GRADE_OPTIONS, 
                                         index=GRADE_OPTIONS.index(current_grade_val) if current_grade_val in GRADE_OPTIONS else 5)
            with c2:
                new_fix = st.number_input("ยอดค่าซ่อมรวมใหม่ (E)", value=int(row['ค่าซ่อม']), step=1, format="%d")
                new_note = st.text_area("บันทึกเพิ่มเติม (K)", value=str(row['หมายเหตุ']) if pd.notna(row['หมายเหตุ']) else "")
            
            if st.form_submit_button("✅ ยืนยันการอัปเดต"):
                total_f = int(row['ต้นทุนซื้อ'] + new_fix)
                profit_h = int(new_sell - total_f) if new_sell > 0 else 0
                
                # Payload ต้องชื่อ "grade" ตัวเล็กตามที่เขียนใน Apps Script
                payload = {
                    "action": "update",
                    "id": str(tid), 
                    "status": new_status, 
                    "fix": int(new_fix), 
                    "total_cost": total_f, 
                    "sell": int(new_sell), 
                    "profit": profit_h, 
                    "note": new_note,
                    "grade": str(new_grade) # ส่งเกรดใหม่ไปบันทึกลงคอลัมน์ L
                }
                
                # ส่งข้อมูลไป URL ใหม่ที่คุณเพิ่ง Deployment
                NEW_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwA88e1uY4rAcErJsUxxbLRnYVscULcd3cSZugt5FByZXopK54FndJ3hZr5HYcGe0-9wQ/exec"
                
                response = requests.post(NEW_SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"บันทึกข้อมูลเรียบร้อย! (เกรดใหม่: {new_grade})")
                    st.cache_data.clear() # ล้างแคชเพื่อให้หน้าจอโหลดค่าใหม่จาก Sheets
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล")

# --- 5. จัดการฐานข้อมูล ---
elif menu == "🗑️ จัดการฐานข้อมูล":
    st.title("🗑️ ระบบลบข้อมูล")
    if not df.empty:
        target = st.selectbox("เลือกรถที่ต้องการลบ:", df.apply(lambda x: f"{x['ID']} | {x['ยี่ห้อ/รุ่น']}", axis=1))
        tid = target.split(" | ")[0]
        confirm = st.checkbox(f"ยืนยันว่าจะลบ ID {tid} จริงๆ")
        if confirm and st.button("🚨 ยืนยันการลบถาวร", type="primary"):
            requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
            st.error("ลบข้อมูลสำเร็จ"); st.cache_data.clear(); time.sleep(1); st.rerun()



# --- เพิ่มเมนูใหม่ใน SIDEBAR ---
menu = st.sidebar.radio("ระบบบริหารจัดการ", 
                        ["📊 แผงควบคุม BI", "🔍 คลังรถยนต์", "📥 ลงทะเบียนรถเข้า", "🔄 อัปเดตสถานะ/ค่าซ่อม", "📋 รายงานและสรุปผล", "🗑️ จัดการฐานข้อมูล"])

# --- 5. รายงานและสรุปผล (ฟีเจอร์ใหม่!) ---
elif menu == "📋 รายงานและสรุปผล":
    st.title("📋 รายงานและสรุปผลธุรกิจ")
    
    tab1, tab2 = st.tabs(["📄 สรุปรายการรถ (Print)", "📈 สรุปยอดขายประจำเดือน"])
    
    with tab1:
        st.subheader("🖨️ สรุปรายการรถในคลัง (พร้อมพิมพ์)")
        # เลือกเฉพาะรถที่ยังไม่ขาย หรือทั้งหมด
        report_type = st.radio("เลือกดูรายการ:", ["เฉพาะรถพร้อมขาย", "รถทั้งหมด"], horizontal=True)
        
        if report_type == "เฉพาะรถพร้อมขาย":
            print_df = df[df['สถานะ'] == 'พร้อมขาย']
        else:
            print_df = df

        if not print_df.empty:
            # จัดรูปแบบตารางให้สวยงามสำหรับการพิมพ์
            display_df = print_df[['ID', 'ยี่ห้อ/รุ่น', 'เกรดรถ', 'สถานะ', 'ต้นทุนรวม', 'ราคาขาย', 'หมายเหตุ']].copy()
            display_df['ต้นทุนรวม'] = display_df['ต้นทุนรวม'].apply(lambda x: f"{x:,.0f} ฿")
            display_df['ราคาขาย'] = display_df['ราคาขาย'].apply(lambda x: f"{x:,.0f} ฿")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.info("💡 คำแนะนำ: คุณสามารถคลิกขวาที่ตารางแล้วเลือก 'Print' หรือใช้ปุ่ม 'Download as CSV' เพื่อนำไปเปิดใน Excel และสั่งพิมพ์ได้ทันทีครับ")
            st.download_button(label="📥 ดาวน์โหลดรายการรถ (CSV)", data=display_df.to_csv(index=False).encode('utf-8-sig'), file_name=f'car_report_{datetime.now().strftime("%d%m%Y")}.csv', mime='text/csv')
        else:
            st.warning("ไม่มีข้อมูลรายการรถ")

    with tab2:
        st.subheader("📅 สรุปยอดขายประจำเดือน")
        # กรองเฉพาะรถที่ขายแล้ว
        sold_df = df[df['สถานะ'] == 'ขายแล้ว'].copy()
        
        if not sold_df.empty:
            # แปลงวันที่เพื่อให้กรองตามเดือนได้
            sold_df['เดือนที่ขาย'] = sold_df['วันที่บันทึก'].dt.strftime('%Y-%m')
            month_list = sorted(sold_df['เดือนที่ขาย'].unique(), reverse=True)
            selected_month = st.selectbox("เลือกเดือนที่ต้องการสรุป:", month_list)
            
            monthly_data = sold_df[sold_df['เดือนที่ขาย'] == selected_month]
            
            # สรุปตัวเลขสำคัญ
            m_col1, m_col2, m_col3 = st.columns(3)
            total_sales = monthly_data['ราคาขาย'].sum()
            total_profit = monthly_data['กำไรสุทธิ'].sum()
            car_count = len(monthly_data)
            
            m_col1.metric("🚗 จำนวนรถที่ขายได้", f"{car_count} คัน")
            m_col2.metric("💰 ยอดขายรวม", f"{int(total_sales):,}")
            m_col3.metric("📈 กำไรสุทธิรวม", f"{int(total_profit):,}", delta=f"{int(total_profit/car_count):,} ต่อคัน" if car_count > 0 else None)
            
            st.markdown("---")
            st.write(f"**รายละเอียดรถที่ปิดการขายในเดือน {selected_month}:**")
            st.table(monthly_data[['ID', 'ยี่ห้อ/รุ่น', 'เกรดรถ', 'ต้นทุนรวม', 'ราคาขาย', 'กำไรสุทธิ']].reset_index(drop=True))
        else:
            st.info("ยังไม่มีข้อมูลรถที่ 'ขายแล้ว' ในระบบ")
