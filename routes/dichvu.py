from datetime import date
from flask import Blueprint, render_template, flash, request, redirect, url_for
from auth import login_required
from db import get_connection

dichvu_bp = Blueprint('dichvu', __name__, url_prefix='/dichvu')


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

    # dữ liệu cho ô đăng ký
    ds_ct, ds_dv_all = [], []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT MaCT, TenCT FROM CONGTY ORDER BY TenCT")
            ds_ct = cur.fetchall()
            cur.execute("SELECT MaDV, TenDV FROM DICHVU ORDER BY TenDV")
            ds_dv_all = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được danh sách công ty/dịch vụ: ' + str(e), 'danger')

    tong = sum(r['TienDV'] or 0 for r in ds)
    return render_template('dichvu.html', ds=ds, thang=thang, nam=nam, tong=tong,
                           tu_khoa=tu_khoa, dv=dv, ds_dichvu=ds_dichvu,
                           ds_congty=ds_congty, ds_ct=ds_ct, ds_dv_all=ds_dv_all,
                           hom_nay=hom_nay.strftime('%Y-%m-%d'))


@dichvu_bp.route('/dangky', methods=['POST'])
@login_required
def them_dang_ky():
    ma_ct = request.form.get('ma_ct', '').strip()
    ma_dv = request.form.get('ma_dv', '').strip()
    ngay = request.form.get('ngay', '').strip()
    thang = request.form.get('thang', '')
    nam = request.form.get('nam', '')

    if not ma_ct or not ma_dv or not ngay:
        flash('Vui lòng chọn đầy đủ công ty, dịch vụ và ngày đăng ký.', 'danger')
    else:
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO DANGKY_DICHVU (MaCT, MaDV, NgayDangKy) "
                    "VALUES (%s, %s, %s)",
                    (ma_ct, ma_dv, ngay)
                )
                conn.commit()
                flash('Đã thêm đăng ký dịch vụ.', 'success')
            finally:
                conn.close()
        except Exception as e:
            flash('Không thêm được: ' + str(e), 'danger')

    return redirect(url_for('dichvu.tien_dich_vu', thang=thang, nam=nam))