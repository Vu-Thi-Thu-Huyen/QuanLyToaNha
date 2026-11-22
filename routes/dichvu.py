from datetime import date, datetime
from flask import Blueprint, render_template, flash, request, redirect, url_for
from auth import login_required
from db import get_connection
from helpers import lay_nhieu, thuc_thi

dichvu_bp = Blueprint('dichvu', __name__, url_prefix='/dichvu')


def _ngay_hop_le(chuoi):
    try:
        datetime.strptime(chuoi, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def _quay_lai():
    """Quay về TAB 3 (danh sách đã đăng ký), giữ nguyên bộ lọc đang dùng."""
    return redirect(url_for('dichvu.quan_ly',
                            q=request.form.get('q') or None,
                            dv=request.form.get('dv') or None))


# ================================================================ TAB 1
@dichvu_bp.route('/')
@login_required
def tien_dich_vu():
    hom_nay = date.today()
    tu_khoa = request.args.get('q', '').strip()
    dv = request.args.get('dv', '').strip()
    try:
        thang = int(request.args.get('thang', hom_nay.month))
        nam = int(request.args.get('nam', hom_nay.year))
        if not 1 <= thang <= 12:
            raise ValueError
    except ValueError:
        flash('Tháng phải từ 1 đến 12 và năm phải là số.', 'danger')
        thang, nam = hom_nay.month, hom_nay.year

    ds = []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.callproc('PR_TIEN_DICHVU_CHITIET', [thang, nam])
            for res in cur.stored_results():
                cols = res.column_names
                ds = [dict(zip(cols, row)) for row in res.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được dữ liệu dịch vụ: ' + str(e), 'danger')

    ds = [r for r in ds if (r['SoNgay'] or 0) > 0]

    ds_dichvu = sorted({r['TenDV'] for r in ds if r['TenDV']})
    if dv not in ds_dichvu:
        dv = ''
    ds_congty = sorted({r['TenCT'] for r in ds if r['TenCT']})

    if tu_khoa:
        kw = tu_khoa.lower()
        ds = [r for r in ds if kw in str(r['TenCT']).lower()]
    if dv:
        ds = [r for r in ds if r['TenDV'] == dv]

    ds.sort(key=lambda r: ((r['TenCT'] or '').lower(), r['TenDV'] or ''))
    tong = sum(r['TienDV'] or 0 for r in ds)
    return render_template('dichvu.html', ds=ds, thang=thang, nam=nam, tong=tong,
                           tu_khoa=tu_khoa, dv=dv, ds_dichvu=ds_dichvu,
                           ds_congty=ds_congty)


# ================================================================ TAB 2 (MỚI)
@dichvu_bp.route('/dang-ky')
@login_required
def dang_ky():
    ds_ct, ds_dv = [], []
    try:
        ds_ct = lay_nhieu("SELECT MaCT, TenCT FROM CONGTY ORDER BY TenCT")
        ds_dv = lay_nhieu(
            "SELECT MaDV, TenDV, LoaiDV, DonGia, BatBuoc FROM DICHVU ORDER BY MaDV")
    except Exception as e:
        flash('Không đọc được dữ liệu: ' + str(e), 'danger')
    return render_template('dichvu_dang_ky.html', ds_ct=ds_ct, ds_dv=ds_dv,
                           hom_nay=date.today().strftime('%Y-%m-%d'))


# ================================================================ TAB 3
@dichvu_bp.route('/quan-ly')
@login_required
def quan_ly():
    hom_nay = date.today()
    tu_khoa = request.args.get('q', '').strip()
    dv = request.args.get('dv', '').strip()

    ds_ct, ds_dv_all, ds_dk = [], [], []
    try:
        ds_ct = lay_nhieu("SELECT MaCT, TenCT FROM CONGTY ORDER BY TenCT")
        ds_dv_all = lay_nhieu("SELECT MaDV, TenDV FROM DICHVU ORDER BY TenDV")
        ds_dk = lay_nhieu(
            "SELECT s.MaSD, c.TenCT, d.TenDV, d.BatBuoc, s.NgayBatDau, s.NgayKetThuc "
            "FROM SUDUNGDICHVU s "
            "JOIN CONGTY c ON c.MaCT = s.MaCT "
            "JOIN DICHVU d ON d.MaDV = s.MaDV "
            "ORDER BY c.TenCT, d.TenDV, s.NgayBatDau")
        if tu_khoa:
            ds_dk = [r for r in ds_dk if tu_khoa.lower() in r['TenCT'].lower()]
        if dv:
            ds_dk = [r for r in ds_dk if r['TenDV'] == dv]
    except Exception as e:
        flash('Không đọc được danh sách đăng ký dịch vụ: ' + str(e), 'danger')

    return render_template('dichvu_quan_ly.html', ds_ct=ds_ct, ds_dv_all=ds_dv_all,
                           dang_ky=ds_dk, tu_khoa=tu_khoa, dv=dv,
                           hom_nay=hom_nay.strftime('%Y-%m-%d'))


# ---------------------------------------------------------------- THÊM đăng ký
@dichvu_bp.route('/dangky', methods=['POST'])
@login_required
def them_dang_ky():
    ten_ct = request.form.get('ten_ct', '').strip()
    ma_dv = request.form.get('ma_dv', '').strip()
    ngay = request.form.get('ngay', '').strip()

    # ô công ty là input gõ/chọn => tra MaCT theo tên
    ma_ct = None
    try:
        for c in lay_nhieu("SELECT MaCT, TenCT FROM CONGTY"):
            if c['TenCT'].strip().lower() == ten_ct.lower():
                ma_ct = c['MaCT']
                break
    except Exception as e:
        flash('Không đọc được danh sách công ty: ' + str(e), 'danger')
        return redirect(url_for('dichvu.dang_ky'))

    if not ten_ct or not ma_dv or not ngay:
        flash('Vui lòng chọn đầy đủ công ty, dịch vụ và ngày bắt đầu.', 'danger')
    elif ma_ct is None:
        flash('Công ty không có trong danh sách, hãy chọn lại.', 'danger')
    elif not _ngay_hop_le(ngay):
        flash('Ngày bắt đầu không hợp lệ.', 'danger')
    else:
        ok, kq = thuc_thi(
            "INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau) VALUES (%s, %s, %s)",
            (ma_ct, ma_dv, ngay))
        flash('Đã thêm đăng ký dịch vụ.' if ok else kq, 'success' if ok else 'danger')

    return redirect(url_for('dichvu.dang_ky'))


# ---------------------------------------------------------------- KẾT THÚC
@dichvu_bp.route('/dangky/<int:ma_sd>/ketthuc', methods=['POST'])
@login_required
def ket_thuc_dang_ky(ma_sd):
    ngay = request.form.get('ngay_ket_thuc', '').strip()
    if not _ngay_hop_le(ngay):
        flash('Vui lòng chọn ngày kết thúc hợp lệ.', 'danger')
    else:
        ok, kq = thuc_thi(
            "UPDATE SUDUNGDICHVU SET NgayKetThuc = %s WHERE MaSD = %s", (ngay, ma_sd))
        flash('Đã kết thúc đăng ký dịch vụ.' if ok else kq, 'success' if ok else 'danger')
    return _quay_lai()


# ---------------------------------------------------------------- XÓA
@dichvu_bp.route('/dangky/<int:ma_sd>/xoa', methods=['POST'])
@login_required
def xoa_dang_ky(ma_sd):
    ok, kq = thuc_thi("DELETE FROM SUDUNGDICHVU WHERE MaSD = %s", (ma_sd,))
    flash('Đã xóa đăng ký dịch vụ.' if ok else kq, 'success' if ok else 'danger')
    return _quay_lai()
