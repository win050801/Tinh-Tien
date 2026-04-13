import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

DATABASE_NAME = 'sales_manager_v5.db'

# ==========================================
# 1. HÀM XỬ LÝ DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (ngay TEXT, ma_hang TEXT, so_don INTEGER, tien_ads REAL, loi_nhuan REAL,
                 PRIMARY KEY (ngay, ma_hang))''')
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (ma_hang TEXT PRIMARY KEY, gia_nhap REAL, gia_ban REAL, phi_don REAL)''')
    
    # Tạo mã mẫu nếu DB trống
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO products VALUES ('Mã Mẫu', 100000, 250000, 5000)")
    conn.commit()
    conn.close()

def get_all_products():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    rows = c.fetchall()
    conn.close()
    hang_dict = {}
    for row in rows:
        hang_dict[row[0]] = {"nhap": row[1], "ban": row[2], "phi": row[3]}
    return hang_dict

def save_product(ma_hang, nhap, ban, phi):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)", (ma_hang, nhap, ban, phi))
    conn.commit()
    conn.close()

def delete_product(ma_hang):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE ma_hang=?", (ma_hang,))
    conn.commit()
    conn.close()

def save_history(ngay, ma_hang, so_don, tien_ads, loi_nhuan):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO history VALUES (?, ?, ?, ?, ?)", 
              (ngay, ma_hang, so_don, tien_ads, loi_nhuan))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql_query("SELECT * FROM history ORDER BY ngay DESC", conn)
    conn.close()
    return df

# Khởi tạo DB
init_db()

# ==========================================
# 2. CẤU HÌNH GIAO DIỆN CHUNG
# ==========================================
st.set_page_config(page_title="Hệ Thống Bán Hàng", layout="wide", page_icon="💼")
st.markdown("<style>[data-testid='stMetricValue'] { font-size: 26px; font-weight: bold; }</style>", unsafe_allow_html=True)

# Kéo dữ liệu mặt hàng mới nhất từ DB
DANH_SACH_HANG = get_all_products()

# ==========================================
# 3. MENU ĐIỀU HƯỚNG (Thay cho Tabs)
# ==========================================
st.sidebar.title("📌 MENU CHÍNH")
# Sử dụng radio button để làm menu, mỗi lần click đổi menu là web tự động F5
chuc_nang = st.sidebar.radio(
    "Vui lòng chọn phân hệ:",
    ["💰 Ghi Nhận Doanh Thu", "📦 Quản Lý Mặt Hàng"]
)

st.sidebar.divider()
st.sidebar.info("💡 **Mẹo:** Mỗi lần bạn chuyển đổi giữa các menu, dữ liệu sẽ tự động được làm mới 100% từ hệ thống.")

# ==========================================
# PHÂN HỆ 1: GHI NHẬN DOANH THU
# ==========================================
if chuc_nang == "💰 Ghi Nhận Doanh Thu":
    st.title("💰 Ghi Nhận Doanh Thu Hôm Nay")
    
    if not DANH_SACH_HANG:
        st.warning("⚠️ Hệ thống chưa có mặt hàng nào. Vui lòng chuyển sang mục 'Quản Lý Mặt Hàng' để thêm mới!")
    else:
        # Khung chọn mã hàng đưa ra giữa cho thoáng
        ma_selected = st.selectbox("👉 Chọn mặt hàng đang bán:", list(DANH_SACH_HANG.keys()))
        info = DANH_SACH_HANG[ma_selected]
        
        st.info(f"**Cấu hình {ma_selected}:** Giá nhập: {info['nhap']:,.0f} đ | Giá bán: {info['ban']:,.0f} đ | Phí đơn: {info['phi']:,.0f} đ")
        
        # Nhập liệu
        c1, c2, c3 = st.columns([1, 1, 1.5])
        with c1:
            today = st.date_input("Ngày bán", date.today())
        with c2:
            quantity = st.number_input("Số lượng đơn", min_value=0, step=1, value=None, placeholder="Nhập số đơn...")
        with c3:
            ads_cost = st.number_input("Tiền Ads (VNĐ)", min_value=0, step=10000, value=None, placeholder="Nhập tiền Ads...")
            if ads_cost: st.caption(f"Định dạng: **{ads_cost:,.0f} đ**")

        # Tính toán
        q = quantity or 0
        a = ads_cost or 0
        loi_nhuan = (q * info['ban']) - (q * (info['nhap'] + info['phi'])) - a

        st.markdown("### 📊 Kết quả tạm tính:")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Doanh thu", f"{(q * info['ban']):,.0f} đ")
        m2.metric("Vốn + Phí", f"{(q * (info['nhap'] + info['phi'])):,.0f} đ")
        m3.metric("Tiền Ads", f"{a:,.0f} đ")
        m4.metric("Lãi dự kiến", f"{loi_nhuan:,.0f} đ")

        if st.button(f"💾 LƯU DOANH THU {ma_selected.upper()}", use_container_width=True, type="primary"):
            if quantity is not None and ads_cost is not None:
                save_history(str(today), ma_selected, q, a, loi_nhuan)
                st.success(f"✅ Đã ghi nhận dữ liệu cho {ma_selected} ngày {today}")
                st.rerun()
            else:
                st.error("Vui lòng điền đủ Số đơn và Tiền Ads!")

        st.divider()
        
        # Bảng Nhật Ký Doanh Thu
        st.subheader("📅 Nhật ký doanh thu gộp theo ngày")
        df_raw = load_history()
        
        if not df_raw.empty:
            # Dàn ngang mã hàng (Pivot)
            df_pivot = df_raw.pivot_table(index='ngay', columns='ma_hang', values='so_don', aggfunc='sum', fill_value=0).reset_index()
            
            # Đảm bảo hiển thị đủ cột các mặt hàng hiện có
            for ma in DANH_SACH_HANG.keys():
                if ma not in df_pivot.columns:
                    df_pivot[ma] = 0

            # Cộng tiền
            df_sums = df_raw.groupby('ngay').agg({'tien_ads': 'sum', 'loi_nhuan': 'sum'}).reset_index()
            df_final = pd.merge(df_pivot, df_sums, on='ngay').sort_values('ngay', ascending=False)
            
            # Sắp xếp cột linh hoạt
            cac_cot_ma_hang = [col for col in df_final.columns if col not in ['ngay', 'tien_ads', 'loi_nhuan']]
            df_final = df_final[['ngay'] + cac_cot_ma_hang + ['tien_ads', 'loi_nhuan']]

            # Hàng TỔNG CỘNG
            total_dict = {'ngay': 'TỔNG CỘNG'}
            for col in cac_cot_ma_hang:
                total_dict[col] = df_final[col].sum()
            total_dict['tien_ads'] = df_final['tien_ads'].sum()
            total_dict['loi_nhuan'] = df_final['loi_nhuan'].sum()
            
            display_df = pd.concat([df_final, pd.DataFrame([total_dict])], ignore_index=True)
            display_df['tien_ads'] = display_df['tien_ads'].apply(lambda x: f"{x:,.0f} đ")
            display_df['loi_nhuan'] = display_df['loi_nhuan'].apply(lambda x: f"{x:,.0f} đ")

            st.dataframe(display_df.rename(columns={'ngay': 'Ngày', 'tien_ads': 'Tổng Tiền Ads', 'loi_nhuan': 'Tổng Lợi Nhuận'}), 
                         use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu bán hàng.")

# ==========================================
# PHÂN HỆ 2: QUẢN LÝ MẶT HÀNG
# ==========================================
elif chuc_nang == "📦 Quản Lý Mặt Hàng":
    st.title("📦 Danh Mục Mặt Hàng")
    
    st.subheader("➕ Thêm mới / Cập nhật giá")
    st.write("- **Thêm mới:** Nhập tên mã hàng chưa từng có vào ô bên dưới.\n- **Sửa giá:** Nhập lại ĐÚNG TÊN mã hàng đã có, hệ thống sẽ tự đè giá mới lên giá cũ.")
    
    with st.form("form_san_pham", clear_on_submit=True):
        col_name, col_nhap, col_ban, col_phi = st.columns(4)
        new_ma = col_name.text_input("Tên Mã Hàng", placeholder="Ví dụ: Áo Thun")
        new_nhap = col_nhap.number_input("Giá Nhập (VNĐ)", min_value=0, step=1000)
        new_ban = col_ban.number_input("Giá Bán (VNĐ)", min_value=0, step=1000)
        new_phi = col_phi.number_input("Phí Đóng Gói (VNĐ)", min_value=0, step=1000)
        
        submitted = st.form_submit_button("💾 LƯU MẶT HÀNG", type="primary", use_container_width=True)
        if submitted:
            if new_ma.strip() == "":
                st.error("❌ Tên mã hàng không được để trống!")
            else:
                save_product(new_ma.strip(), new_nhap, new_ban, new_phi)
                st.success(f"✅ Đã lưu cấu hình cho mặt hàng: {new_ma}")
                st.rerun()

    st.divider()
    st.subheader("📋 Bảng Giá & Chi Phí Hiện Tại")
    
    if DANH_SACH_HANG:
        list_hang = []
        for ma, gia in DANH_SACH_HANG.items():
            list_hang.append({
                "Tên Mã Hàng": ma,
                "Giá Nhập": f"{gia['nhap']:,.0f} đ",
                "Giá Bán": f"{gia['ban']:,.0f} đ",
                "Phí Đóng Gói": f"{gia['phi']:,.0f} đ"
            })
        st.dataframe(pd.DataFrame(list_hang), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        with st.expander("🗑️ Khu vực nguy hiểm (Xóa mặt hàng)"):
            st.warning("Việc xóa mã hàng sẽ làm mã này biến mất khỏi danh sách chọn khi Ghi nhận doanh thu. (Lịch sử bán cũ vẫn được giữ nguyên).")
            del_ma = st.selectbox("Chọn mã cần xóa", list(DANH_SACH_HANG.keys()))
            if st.button("XÁC NHẬN XÓA"):
                delete_product(del_ma)
                st.success(f"Đã xóa mặt hàng {del_ma} khỏi hệ thống.")
                st.rerun()
    else:
        st.info("Chưa có mặt hàng nào.")