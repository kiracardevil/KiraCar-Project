import streamlit as st
import pandas as pd
import requests
import streamlit as st
import pandas as pd
import requests
import streamlit as st
import pandas as pd
import requests

# --- ส่วนที่ 1: วางตัวแปร URL ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRTaXnMfRxy-JdgCp4rCqJzdUES16l77D8_Okbf-bQnjxnu5HeRyS5agIokGCfG_3x3oCK7VCdlGXG2/pub?gid=754879556&single=true&output=csv"

# --- ส่วนที่ 2: วางฟังก์ชันนี้ไว้ตรงนี้ (Copy ไปแปะได้เลย) ---
def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
    payload = {
        "entry.1392091793": model,
        "entry.1772417832": buy_price,
        "entry.499287053": repair_cost,
        "entry.50844596": status,
        "entry.1300688537": sell_price,
    }
    try:
        # ส่งข้อมูลแบบเงียบๆ ไม่ต้อง Login
        requests.post(FORM_URL, data=payload)
        return True
    except:
        return False

# --- ส่วนที่ 3: เริ่มหน้าตาโปรแกรม ---
st.title("🚗 KiraCar Pro Management")
# ... โค้ดส่วนที่เหลือ ...
# --- 1. ส่วนตั้งค่า URL (วางไว้บนสุด) ---
FORM_URL = "https://docs.google.com/forms/d/e/.../formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/.../pub?output=csv"

# --- 2. วางโค้ดฟังก์ชันที่คุณถามไว้ตรงนี้ครับ ---
def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
    payload = {
        "entry.1392091793": model,
        "entry.1772417832": buy_price,
        "entry.499287053": repair_cost,
        "entry.50844596": status,
        "entry.1300688537": sell_price,
    }
    try:
        # ใช้ requests.post เพื่อส่งข้อมูลไปที่ Google Form
        response = requests.post(FORM_URL, data=payload)
        return True # ถ้าส่งสำเร็จ
    except:
        return False # ถ้าส่งไม่สำเร็จ

# --- 3. ส่วนการทำงานของหน้าเว็บ (เรียกใช้ฟังก์ชันด้านบน) ---
st.title("KiraCar Pro")

# เมื่อผู้ใช้กดปุ่มในฟอร์ม เราจะเรียกใช้ฟังก์ชันที่เราวางไว้ด้านบนแบบนี้:
if st.button("บันทึกข้อมูล"):
    success = save_to_google_form(model, buy, repair, status, sell) # เรียกใช้งาน
    if success:
        st.success("บันทึกสำเร็จ!")
import plotly.express as px
from datetime import datetime

# --- การตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="KiraCar Pro Plus", layout="wide", page_icon="🏎️")

# 1. ข้อมูลการเชื่อมต่อ (เดิม)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeX3tFW6TrfVY1MbWXFW1WzzpeIefrRwwg75HynBd2Mnkg06g/formResponse"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRTaXnMfRxy-JdgCp4rCqJzdUES16l77D8_Okbf-bQnjxnu5HeRyS5agIokGCfG_3x3oCK7VCdlGXG2/pub?gid=754879556&single=true&output=csv"

def save_to_google_form(model, buy_price, repair_cost, status, sell_price):
    payload = {
        "entry.1392091793": model,
        "entry.1772417832": buy_price,
        "entry.499287053": repair_cost,
        "entry.50844596": status,
        "entry.1300688537": sell_price,
    }
    try:
        requests.post(FORM_URL, data=payload)
        return True
    except:
        return False

# --- โหลดข้อมูลและเตรียม Data ---
@st.cache_data(ttl=60) # รีเฟรชทุก 1 นาที
def load_data():
    try:
        data = pd.read_csv(SHEET_CSV_URL)
        data.columns = ['Timestamp', 'รุ่นรถ', 'ราคาทุน', 'ค่าซ่อม', 'สถานะ', 'ราคาขาย']
        data['ราคาทุน'] = pd.to_numeric(data['ราคาทุน'], errors='coerce').fillna(0)
        data['ค่าซ่อม'] = pd.to_numeric(data['ค่าซ่อม'], errors='coerce').fillna(0)
        data['ราคาขาย'] = pd.to_numeric(data['ราคาขาย'], errors='coerce').fillna(0)
        data['ทุนรวม'] = data['ราคาทุน'] + data['ค่าซ่อม']
        data['กำไรสุทธิ'] = data['ราคาขาย'] - data['ทุนรวม']
        return data
    except:
        return pd.DataFrame()

df = load_data()

# --- ส่วนหน้าตาโปรแกรม ---
st.title("🏎️ KiraCar Pro: Smart Inventory Management")

# Sidebar Menu
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/743/743231.png", width=100)
menu = st.sidebar.radio("เมนูหลัก", ["📊 ระบบวิเคราะห์ Dashboard", "➕ บันทึกรถเข้าใหม่", "🔎 ค้นหาและกรองข้อมูล"])

if menu == "📊 ระบบวิเคราะห์ Dashboard":
    if not df.empty:
        # ส่วนตัวเลขสรุป (KPIs)
        total_cars = len(df)
        total_inv = df['ทุนรวม'].sum()
        total_profit = df[df['สถานะ'] == 'ขายแล้ว']['กำไรสุทธิ'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 รถทั้งหมด", f"{total_cars} คัน")
        col2.metric("💰 เงินทุนหมุนเวียน", f"{total_inv:,.0f} ฿")
        col3.metric("📈 กำไรที่รับมาแล้ว", f"{total_profit:,.0f} ฿", delta_color="normal")
        col4.metric("✨ อัตรากำไรเฉลี่ย", f"{(total_profit/total_inv*100 if total_inv > 0 else 0):.1f} %")

        st.markdown("---")
        
        # ส่วนกราฟ
        c1, c2 = st.columns([6, 4])
        with c1:
            st.subheader("📈 แนวโน้มกำไรรายคัน")
            fig_bar = px.bar(df, x='รุ่นรถ', y='กำไรสุทธิ', color='สถานะ', 
                             title="กำไรเปรียบเทียบแต่ละคัน", text_auto='.2s')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.subheader("🛒 สัดส่วนสต็อก")
            fig_pie = px.pie(df, names='สถานะ', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.info("ยังไม่มีข้อมูล กรุณาไปที่เมนู 'บันทึกรถเข้าใหม่'")

elif menu == "➕ บันทึกรถเข้าใหม่":
    st.subheader("📋 ลงทะเบียนรถคันใหม่เข้าสู่ระบบ")
    with st.form("pro_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            model = st.text_input("ชื่อรุ่นรถ/ปี", placeholder="เช่น Honda Civic FE 2022")
            buy = st.number_input("ราคาทุนซื้อ", min_value=0, step=5000)
            repair = st.number_input("งบประมาณปรับสภาพ", min_value=0, step=1000)
        with c2:
            status = st.selectbox("สถานะแรกเริ่ม", ["กำลังซ่อม", "พร้อมขาย", "จองแล้ว", "ขายแล้ว"])
            sell = st.number_input("ราคาขายที่ตั้งไว้", min_value=0, step=5000)
            note = st.text_area("หมายเหตุเพิ่มเติม", placeholder="ระบุตำหนิหรือรายการที่ซ่อมไป")

        if st.form_submit_button("🚀 ยืนยันการบันทึกข้อมูล"):
            if model:
                if save_to_google_form(model, buy, repair, status, sell):
                    st.success(f"ระบบบันทึก {model} สำเร็จ! ข้อมูลจะปรากฏในระบบภายใน 1 นาที")
                    st.balloons()
                else:
                    st.error("การส่งข้อมูลขัดข้อง")
            else:
                st.warning("กรุณาใส่ชื่อรุ่นรถ")

elif menu == "🔎 ค้นหาและกรองข้อมูล":
    st.subheader("📂 จัดการและตรวจสอบข้อมูลละเอียด")
    
    # ตัวกรองข้อมูล
    search_query = st.text_input("🔍 ค้นหาตามชื่อรุ่นรถ...")
    filter_status = st.multiselect("เลือกสถานะที่ต้องการดู:", options=df['สถานะ'].unique(), default=df['สถานะ'].unique())
    
    filtered_df = df[df['สถานะ'].isin(filter_status)]
    if search_query:
        filtered_df = filtered_df[filtered_df['รุ่นรถ'].str.contains(search_query, case=False)]
    
    # ตารางแบบ Interactive
    st.dataframe(filtered_df.style.highlight_max(axis=0, subset=['กำไรสุทธิ'], color='#90EE90')
                 .highlight_min(axis=0, subset=['กำไรสุทธิ'], color='#FFB6C1'), 
                 use_container_width=True)
    
    # ระบบส่งออกข้อมูล
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 ดาวน์โหลดรายการที่เลือกเป็น Excel", data=csv, file_name="kiracar_data.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.caption("KiraCar Pro Plus v2.0")


