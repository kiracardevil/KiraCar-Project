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

# --- CSS เพื่อความสวยงาม ---
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
        # ใช้ค่าจากคอลัมน์ 'ต้นทุนรวม' (F) ใน Sheets ได้เลย หรือคำนวณใหม่เพื่อความชัวร์
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
menu = st.sidebar.radio("เมนูบริหารจัดการ", ["💎 แผงควบคุม BI", "🔍 ค้นหา & วิเคราะห์รถ", "📥 บันทึกรถเข้า", "🗑️ ล้างฐานข้อมูล"])

# --- 1. แผงควบคุม BI ---
if menu == "💎 แผงควบคุม BI":
    st.title("💎 Business Intelligence Dashboard")
    
    if not df.empty:
        # ปุ่มดาวน์โหลด Excel
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 ดาวน์โหลดรายงาน Excel (CSV)", data=csv, file_name=f'KiraCar_Report_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

        cols = st.columns(4)
        cols[0].metric("💰 กำไรสะสมสุทธิ", f"{df['กำไรสุทธิ'].sum():,.0f}", "THB")
        avg_turnover = df[df['สถานะ']=='ขายแล้ว']['อายุสต็อก'].mean()
        cols[1].metric("⏱️ ปิดการขายเฉลี่ย", f"{avg_turnover:.1f} วัน")
        total_inv = df[df['สถานะ']!='ขายแล้ว']['ต้นทุนรวม'].sum()
        cols[2].metric("📦 มูลค่าสินค้าคงคลัง", f"{total_inv:,.0f}", "THB")
        win_rate = (len(df[df['สถานะ']=='ขายแล้ว']) / len(df) * 100) if len(df)>0 else 0
        cols[3].metric("📈 อัตราการขายออก", f"{win_rate:.1f}%")

        st.markdown("---")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("📊 กำไรแยกตามเกรดรถ (A/B/C)")
            if 'เกรดรถ' in df.columns and not df.empty:
                try:
                    # เตรียมข้อมูลสำหรับ Sunburst
                    temp_df = df.copy()
                    temp_df['เกรดรถ'] = temp_df['เกรดรถ'].fillna('N/A')
                    temp_df['สถานะ'] = temp_df['สถานะ'].fillna('N/A')
                    
                    # Sunburst แสดงผลได้เฉพาะค่าที่เป็นบวก (กรองค่าที่กำไรเป็น 0 หรือติดลบออกเพื่อไม่ให้กราฟ Error)
                    plot_df = temp_df[temp_df['กำไรสุทธิ'] > 0]
                    
                    if not plot_df.empty:
                        fig_grade = px.sunburst(
                            plot_df, 
                            path=['เกรดรถ', 'สถานะ'], 
                            values='กำไรสุทธิ', 
                            color='เกรดรถ',
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        # เพิ่มการแสดงตัวเลขเงินในกราฟ
                        fig_grade.update_traces(textinfo="label+value")
                        st.plotly_chart(fig_grade, use_container_width=True)
                    else:
                        st.info("ยังไม่มีข้อมูลกำไรที่เป็นบวกเพื่อแสดงกราฟ")
                except:
                    st.warning("โครงสร้างข้อมูลไม่เพียงพอสำหรับสร้างกราฟ Sunburst")
            else:
                st.info("💡 แนะนำ: เพิ่มคอลัมน์ 'เกรดรถ' และข้อมูลใน Sheets")
        with c2:
            st.subheader("🔥 Inventory Velocity")
            sold_cars = df[df['สถานะ']=='ขายแล้ว']
            if not sold_cars.empty:
                brand_speed = sold_cars.groupby('ยี่ห้อ/รุ่น')['อายุสต็อก'].mean().sort_values().reset_index()
                fig_speed = px.bar(brand_speed.head(5), x='อายุสต็อก', y='ยี่ห้อ/รุ่น', orientation='h', color='อายุสต็อก')
                st.plotly_chart(fig_speed, use_container_width=True)

# --- 2. ค้นหา & วิเคราะห์รถ ---
elif menu == "🔍 ค้นหา & วิเคราะห์รถ":
    st.title("🔍 ค้นหาและประเมินราคารถ")
    sort_by = st.selectbox("จัดเรียงตาม:", ["ล่าสุด", "กำไรสูงสุด", "จอดนานที่สุด", "ต้นทุนรวมต่ำสุด"])
    
    if not df.empty:
        if sort_by == "กำไรสูงสุด": df = df.sort_values('กำไรสุทธิ', ascending=False)
        elif sort_by == "จอดนานที่สุด": df = df.sort_values('อายุสต็อก', ascending=False)
        elif sort_by == "ต้นทุนรวมต่ำสุด": df = df.sort_values('ต้นทุนรวม', ascending=True)

        search = st.text_input("🔍 ค้นหารุ่นรถที่ต้องการ...")
        filtered = df[df['ยี่ห้อ/รุ่น'].str.contains(search, case=False)] if search else df

        for _, row in filtered.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    img = row['ลิงก์รูปภาพ'] if pd.notna(row['ลิงก์รูปภาพ']) else "https://via.placeholder.com/250"
                    st.image(img, use_column_width=True)
                with col2:
                    st.markdown(f"### {row['ยี่ห้อ/รุ่น']} <span style='font-size:14px; background:#e1f5fe; padding:2px 8px; border-radius:5px;'>ID: {row['ID']}</span>", unsafe_allow_html=True)
                    
                    # แบ่งเป็น 4 คอลัมน์ย่อยเพื่อให้โชว์ครบทั้ง ราคาขาย, ทุนซื้อ, ค่าซ่อม และ ROI
                    sub1, sub2, sub3, sub4 = st.columns(4)
                    sub1.write(f"**💰 ราคาขาย:**\n{row['ราคาขาย']:,.0f}")
                    sub2.write(f"**💵 ทุนซื้อ:**\n{row['ต้นทุนซื้อ']:,.0f}")
                    sub3.write(f"**🛠️ ค่าซ่อม:**\n{row['ค่าซ่อม']:,.0f}")
                    sub4.write(f"**📈 ROI:**\n{row['ROI (%)']:.1f}%")
                    
                    st.write(f"**📊 ต้นทุนรวม (F):** {row['ต้นทุนรวม']:,.0f} ฿")
                    
                    if row['สถานะ'] != 'ขายแล้ว' and row['อายุสต็อก'] > 45:
                        st.error(f"⚠️ จอดมา {row['อายุสต็อก']} วันแล้ว แนะนำให้รีบระบายออก")
                    
                    st.info(f"📝 **หมายเหตุ:** {row['หมายเหตุ']}")
                st.markdown("---")

# --- 3. บันทึกรถเข้า (ปรับตามลำดับใหม่) ---
elif menu == "📥 บันทึกรถเข้า":
    st.title("📥 ลงทะเบียนรถยนต์ (ระบบคำนวณต้นทุนรวม F อัตโนมัติ)")
    with st.form("enterprise_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("ยี่ห้อ / รุ่น")
            buy = st.number_input("ราคาทุนซื้อ (D)", min_value=0)
            fix = st.number_input("ค่าซ่อม (E)", min_value=0)
        with c2:
            status = st.selectbox("สถานะ (C)", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"])
            sell = st.number_input("ราคาขายตั้งเป้า (G)", min_value=0)
            grade = st.select_slider("เกรดสภาพรถ (L)", options=["C", "B", "B+", "A", "A+"])
        with c3:
            img = st.text_input("ลิงก์รูปภาพ (J)")
            note = st.text_area("หมายเหตุเชิงลึก (K)")
            
        if st.form_submit_button("🚀 บันทึกข้อมูล"):
            total_cost = buy + fix # คำนวณเพื่อลงช่อง F
            profit = sell - total_cost if sell > 0 else 0 # คำนวณเพื่อลงช่อง H
            
            # ลำดับข้อมูล 12 คอลัมน์ (A ถึง L)
            new_data = [
                len(df)+1,     # A: ID
                name,          # B: ยี่ห้อ/รุ่น
                status,        # C: สถานะ
                buy,           # D: ต้นทุนซื้อ
                fix,           # E: ค่าซ่อม
                total_cost,    # F: ต้นทุนรวม *** เป้าหมายของคุณ
                sell,          # G: ราคาขาย
                profit,        # H: กำไรสุทธิ
                datetime.now().strftime("%Y-%m-%d %H:%M"), # I: วันที่
                img,           # J: ลิงก์รูปภาพ
                note,          # K: หมายเหตุ
                grade          # L: เกรดรถ
            ]
            requests.post(SCRIPT_URL, json=new_data)
            st.balloons()
            st.success(f"บันทึกสำเร็จ! ต้นทุนรวมคันนี้คือ {total_cost:,.0f} ฿")
            time.sleep(1)
            st.rerun()

# --- 4. ลบข้อมูล ---
elif menu == "🗑️ ล้างฐานข้อมูล":
    st.title("🗑️ Database Management")
    if not df.empty:
        st.warning("ระวัง: การลบข้อมูลจะไม่สามารถกู้คืนได้")
        
        # 1. เลือกรายการ
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} (ทุน: {x['ต้นทุนรวม']:,.0f})", axis=1).tolist()
        target = st.selectbox("เลือกข้อมูลที่ต้องการลบ:", target_list)
        
        # 2. กางรายละเอียดก่อนลบเพื่อความชัวร์
        tid = target.split(" | ")[0].split(": ")[1]
        target_row = df[df['ID'].astype(str) == tid].iloc[0]
        
        st.info(f"รายการที่เลือก: {target_row['ยี่ห้อ/รุ่น']} | สถานะ: {target_row['สถานะ']}")
        
        # 3. ระบบยืนยันตัวตน (Checkmark ยืนยัน)
        confirm_check = st.checkbox(f"ยืนยันว่าต้องการลบ ID {tid} นี้ออกจากระบบจริงๆ")
        
        if confirm_check:
            if st.button("🚨 ยืนยันการลบถาวร", type="primary"):
                try:
                    # ส่งคำสั่งลบไปยัง Apps Script
                    response = requests.post(SCRIPT_URL, json={"action": "delete", "id": tid})
                    if response.status_code == 200:
                        st.error(f"ทำการลบข้อมูล ID {tid} เรียบร้อยแล้ว")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            st.info("กรุณาติ๊กถูกที่ช่องยืนยันด้านบนเพื่อปลดล็อคปุ่มลบ")
    else:
        st.info("ไม่มีข้อมูลในฐานข้อมูล")

# เพิ่ม "🔄 อัปเดตสถานะรถ" เข้าไปในลิสต์เมนู sidebar ก่อนนะครับ
# menu = st.sidebar.radio("เมนูบริหารจัดการ", ["...", "🔄 อัปเดตสถานะรถ", "..."])

# --- 5. อัปเดตสถานะรถ ---
elif menu == "🔄 อัปเดตสถานะรถ":
    st.title("🔄 อัปเดตสถานะและบันทึกการขาย")
    if not df.empty:
        # 1. เลือกรถที่ต้องการอัปเดต
        target_list = df.apply(lambda x: f"ID: {x['ID']} | {x['ยี่ห้อ/รุ่น']} (สถานะปัจจุบัน: {x['สถานะ']})", axis=1).tolist()
        target = st.selectbox("เลือกรถที่ต้องการเปลี่ยนสถานะ:", target_list)
        
        tid = target.split(" | ")[0].split(": ")[1]
        target_row = df[df['ID'].astype(str) == tid].iloc[0]

        with st.form("update_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.selectbox("เปลี่ยนสถานะเป็น:", ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"], 
                                          index=["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"].index(target_row['สถาน e'] if target_row['สถานะ'] in ["กำลังซ่อม", "พร้อมขาย", "ขายแล้ว"] else 0))
                new_sell_price = st.number_input("ราคาขายจริง (แก้ไขได้)", value=float(target_row['ราคาขาย']), min_value=0.0)
            
            with col2:
                new_fix_cost = st.number_input("ค่าซ่อมเพิ่มเติม (ถ้ามี)", value=float(target_row['ค่าซ่อม']), min_value=0.0)
                new_note = st.text_area("อัปเดตหมายเหตุ", value=target_row['หมายเหตุ'])

            if st.form_submit_button("✅ ยืนยันการอัปเดตข้อมูล"):
                # คำนวณกำไรใหม่ทันที
                total_cost = float(target_row['ต้นทุนซื้อ']) + new_fix_cost
                new_profit = new_sell_price - total_cost if new_status == "ขายแล้ว" else 0
                
                # ส่งข้อมูลไปอัปเดต (ต้องใช้ฟังก์ชัน update ใน Apps Script)
                update_data = {
                    "action": "update",
                    "id": tid,
                    "status": new_status,
                    "fix": new_fix_cost,
                    "total_cost": total_cost,
                    "sell": new_sell_price,
                    "profit": new_profit,
                    "note": new_note
                }
                
                response = requests.post(SCRIPT_URL, json=update_data)
                if response.status_code == 200:
                    st.balloons()
                    st.success(f"อัปเดต {target_row['ยี่ห้อ/รุ่น']} เป็น '{new_status}' เรียบร้อย!")
                    time.sleep(1.5)
                    st.rerun()
    else:
        st.info("ไม่มีข้อมูลรถในระบบ")

