import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import streamlit.components.v1 as components

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
DATABASE_NAME = 'sales_manager_v10.db' # Vẫn dùng DB v10 để không mất dữ liệu cũ của bạn

enter_to_tab_js = """
<script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(e.target);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault();
                inputs[index + 1].focus();
            }
        }
    });
</script>
"""

# ==========================================
# 1. HÀM XỬ LÝ DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (ngay TEXT, ma_hang TEXT, so_don INTEGER, so_hoan INTEGER, tien_ads REAL, loi_nhuan REAL,
                 gia_nhap REAL, gia_ban REAL, phi_san REAL,
                 PRIMARY KEY (ngay, ma_hang))''')
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (ma_hang TEXT PRIMARY KEY, gia_nhap REAL, gia_ban REAL, phi_don REAL)''')
    conn.commit()
    conn.close()

def get_products_df():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df

def save_product(ma, nhap, ban, phi):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)", (ma, nhap, ban, phi))
    conn.commit()
    conn.close()

def delete_product(ma):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE ma_hang=?", (ma,))
    conn.commit()
    conn.close()

def save_smart_history(ngay, ma_hang, input_q, input_h, input_a, current_info):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    
    c.execute("SELECT so_don, so_hoan, tien_ads, gia_nhap, gia_ban, phi_san FROM history WHERE ngay=? AND ma_hang=?", (ngay, ma_hang))
    existing = c.fetchone()

    if existing:
        old_q, old_h, old_a, used_nhap, used_ban, used_phi = existing
    else:
        old_q, old_h, old_a = 0, 0, 0
        used_nhap, used_ban, used_phi = current_info['nhap'], current_info['ban'], current_info['phi']

    final_q = input_q if input_q is not None else old_q
    final_h = input_h if input_h is not None else old_h
    final_a = input_a if input_a is not None else old_a

    if final_h > final_q:
        conn.close()
        return False, f"Lỗi: Số đơn hoàn ({final_h}) > đơn bán ({final_q})."

    so_don_thanh_cong = final_q - final_h
    lai_thuc = (so_don_thanh_cong * used_ban) - (so_don_thanh_cong * (used_nhap + used_phi)) - final_a

    c.execute("INSERT OR REPLACE INTO history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              (ngay, ma_hang, final_q, final_h, final_a, lai_thuc, used_nhap, used_ban, used_phi))
        
    conn.commit()
    conn.close()
    return True, "✅ Đã lưu dữ liệu thành công!"

def load_history():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql_query("SELECT * FROM history ORDER BY ngay DESC", conn)
    conn.close()
    return df

init_db()

# ==========================================
# 2. GIAO DIỆN NGƯỜI DÙNG
# ==========================================
st.set_page_config(page_title="Hệ Thống Quản Lý Bán Hàng", layout="wide", page_icon="💼")
st.markdown("<style>[data-testid='stMetricValue'] { font-size: 26px; font-weight: bold; }</style>", unsafe_allow_html=True)
components.html(enter_to_tab_js, height=0)

df_p = get_products_df()
DANH_SACH_HANG = {row['ma_hang']: {"nhap": row['gia_nhap'], "ban": row['gia_ban'], "phi": row['phi_don']} for _, row in df_p.iterrows()}

st.sidebar.title("📌 MENU CHÍNH")
chuc_nang = st.sidebar.radio("Vui lòng chọn phân hệ:", ["💰 Ghi Nhận Doanh Thu", "📦 Quản Lý Mặt Hàng"])
st.sidebar.divider()

# ==========================================
# PHÂN HỆ 1: GHI NHẬN DOANH THU
# ==========================================
if chuc_nang == "💰 Ghi Nhận Doanh Thu":
    st.title("💰 Doanh Thu & Hàng Hoàn")
    if not DANH_SACH_HANG:
        st.warning("⚠️ Chưa có mặt hàng nào. Vui lòng chuyển sang mục 'Quản Lý Mặt Hàng'!")
    else:
        c_ma, c_ngay = st.columns([2, 1])
        with c_ma:
            ma_selected = st.selectbox("👉 Chọn mã hàng:", list(DANH_SACH_HANG.keys()))
        with c_ngay:
            ngay = st.date_input("Ngày giao dịch", date.today())
            
        info = DANH_SACH_HANG[ma_selected]
        
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute("SELECT gia_nhap, gia_ban, phi_san, so_don, so_hoan, tien_ads FROM history WHERE ngay=? AND ma_hang=?", (str(ngay), ma_selected))
        hist_record = c.fetchone()
        conn.close()

        if hist_record:
            used_nhap, used_ban, used_phi, old_q, old_h, old_a = hist_record
            st.warning(f"🔒 **Đang sử dụng GIÁ CŨ đã chốt của ngày {ngay}:** Nhập {used_nhap:,.0f}đ | Bán {used_ban:,.0f}đ | Phí Sàn {used_phi:,.0f}đ")
        else:
            used_nhap, used_ban, used_phi = info['nhap'], info['ban'], info['phi']
            old_q, old_h, old_a = 0, 0, 0
            st.info(f"🆕 **Sử dụng giá mới nhất:** Nhập {used_nhap:,.0f}đ | Bán {used_ban:,.0f}đ | Phí Sàn {used_phi:,.0f}đ")
        
        if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
        c1, c2, c3 = st.columns(3)
        with c1: q = st.number_input("Số đơn mới (+)", min_value=0, step=1, value=None, key=f"q_{st.session_state.reset_counter}", placeholder="Để trống nếu không đổi")
        with c2: h = st.number_input("Số đơn HOÀN (-)", min_value=0, step=1, value=None, key=f"h_{st.session_state.reset_counter}", placeholder="Để trống nếu không đổi")
        with c3: a = st.number_input("Tiền Ads (VNĐ)", min_value=0, step=10000, value=None, key=f"a_{st.session_state.reset_counter}", placeholder="Để trống nếu không đổi")

        temp_q = q if q is not None else old_q
        temp_h = h if h is not None else old_h
        temp_a = a if a is not None else old_a
        temp_thanh_cong = temp_q - temp_h if temp_q >= temp_h else 0
        
        doanh_thu_tam = temp_thanh_cong * used_ban
        von_va_phi_tam = temp_thanh_cong * (used_nhap + used_phi)
        lai_tam = doanh_thu_tam - von_va_phi_tam - temp_a

        st.markdown("### 📊 Kết quả biến động (Tạm tính):")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Doanh thu (Trừ hoàn)", f"{doanh_thu_tam:,.0f} đ")
        m2.metric("Vốn + Phí Sàn", f"{von_va_phi_tam:,.0f} đ")
        m3.metric("Tiền Ads", f"{temp_a:,.0f} đ")
        m4.metric("Lãi / Lỗ dự kiến", f"{lai_tam:,.0f} đ")

        if st.button(f"💾 LƯU DỮ LIỆU {ma_selected.upper()}", use_container_width=True, type="primary"):
            if q is None and h is None and a is None: st.error("❌ Chưa nhập giá trị!")
            else:
                success, message = save_smart_history(str(ngay), ma_selected, q, h, a, info)
                if success:
                    st.session_state.reset_counter += 1
                    st.success(message)
                    st.rerun()
                else: st.error(message)

        st.divider()
        df_raw = load_history()
        
        if not df_raw.empty:
            # 1. Vẽ Bảng
            st.subheader("📅 Nhật ký doanh thu tổng hợp")
            df_sums = df_raw.groupby('ngay').agg({'so_don': 'sum', 'so_hoan': 'sum', 'tien_ads': 'sum', 'loi_nhuan': 'sum'}).reset_index()
            df_details = df_raw.groupby('ngay').apply(lambda x: ", ".join([f"{m}: {int(s)} (-{int(h)})" for m, s, h in zip(x['ma_hang'], x['so_don'], x['so_hoan']) if s > 0 or h > 0])).reset_index(name='chi_tiet')
            df_final = pd.merge(df_sums, df_details, on='ngay').sort_values('ngay', ascending=False)
            
            total_row = pd.DataFrame({'ngay': ['TỔNG CỘNG'], 'chi_tiet': ['-'], 'so_don': [df_final['so_don'].sum()], 'so_hoan': [df_final['so_hoan'].sum()], 'tien_ads': [df_final['tien_ads'].sum()], 'loi_nhuan': [df_final['loi_nhuan'].sum()]})
            res_df = pd.concat([df_final, total_row], ignore_index=True)
            res_df['tien_ads'] = res_df['tien_ads'].apply(lambda x: f"{x:,.0f} đ")
            res_df['loi_nhuan'] = res_df['loi_nhuan'].apply(lambda x: f"{x:,.0f} đ")
            
            st.dataframe(res_df.rename(columns={'ngay': 'Ngày', 'chi_tiet': 'Mã: Bán (-Hoàn)', 'so_don': 'Tổng Bán', 'so_hoan': 'Tổng Hoàn', 'tien_ads': 'Tổng Ads', 'loi_nhuan': 'Tổng Lãi'}), use_container_width=True, hide_index=True)

            # 2. VẼ BIỂU ĐỒ ĐA ĐƯỜNG (MỚI)
            st.divider()
            st.subheader("📈 Biểu đồ Lợi Nhuận theo từng mặt hàng")
            
            # Xoay trục dữ liệu gốc: Lấy Ngày làm trục X, Mã hàng làm Cột, Lợi nhuận làm Giá trị
            chart_data = df_raw.pivot_table(index='ngay', columns='ma_hang', values='loi_nhuan', aggfunc='sum', fill_value=0)
            
            # Streamlit sẽ tự động vẽ mỗi mã hàng thành 1 đường màu khác nhau
            st.line_chart(chart_data)
            
        else:
            st.info("Chưa có dữ liệu bán hàng.")

# ==========================================
# PHÂN HỆ 2: QUẢN LÝ MẶT HÀNG
# ==========================================
elif chuc_nang == "📦 Quản Lý Mặt Hàng":
    st.title("📦 Quản Lý & Chỉnh Sửa Mặt Hàng")
    
    with st.expander("➕ Thêm mặt hàng mới"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            n_ma = c1.text_input("Tên Mã Hàng")
            n_nhap = c2.number_input("Giá Nhập", min_value=0, step=1000)
            n_ban = c3.number_input("Giá Bán", min_value=0, step=1000)
            n_phi = c4.number_input("Phí Sàn", min_value=0, step=1000)
            if st.form_submit_button("Lưu mặt hàng mới"):
                if n_ma:
                    save_product(n_ma.strip(), n_nhap, n_ban, n_phi)
                    st.rerun()

    st.divider()
    st.subheader("📝 Bảng Chỉnh Sửa Trực Tiếp")
    st.write("Sửa số trên bảng và nhấn **Lưu tất cả thay đổi**. Các ngày cũ đã nhập doanh thu sẽ KHÔNG bị ảnh hưởng bởi bảng giá mới này.")

    df_products = get_products_df()
    if not df_products.empty:
        edited_df = st.data_editor(
            df_products,
            column_config={
                "ma_hang": st.column_config.TextColumn("Tên Mã Hàng", disabled=True),
                "gia_nhap": st.column_config.NumberColumn("Giá Nhập (đ)", format="%d"),
                "gia_ban": st.column_config.NumberColumn("Giá Bán (đ)", format="%d"),
                "phi_don": st.column_config.NumberColumn("Phí Sàn (đ)", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
            key="product_editor"
        )

        if st.button("💾 LƯU TẤT CẢ THAY ĐỔI TỪ BẢNG", type="primary", use_container_width=True):
            conn = sqlite3.connect(DATABASE_NAME)
            c = conn.cursor()
            for _, row in edited_df.iterrows():
                c.execute("UPDATE products SET gia_nhap=?, gia_ban=?, phi_don=? WHERE ma_hang=?", 
                          (row['gia_nhap'], row['gia_ban'], row['phi_don'], row['ma_hang']))
            conn.commit()
            conn.close()
            st.success("🎉 Đã cập nhật bảng giá mới nhất!")
            st.rerun()

        st.markdown("---")
        with st.expander("🗑️ Xóa mặt hàng"):
            del_ma = st.selectbox("Chọn mã cần xóa hoàn toàn:", df_products['ma_hang'].tolist())
            if st.button("XÁC NHẬN XÓA MÃ NÀY"):
                delete_product(del_ma)
                st.rerun()
    else:
        st.info("Chưa có mặt hàng nào.")