from datetime import date
from flask import Blueprint, render_template, flash, request
from auth import login_required
from db import get_connection

luong_bp = Blueprint('luong', __name__, url_prefix='/luong')


@luong_bp.route('/')
@login_required
def bang_luong():
    hom_nay = date.today()
    tu_khoa = request.args.get('q', '').strip()
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
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT v.MaNV, v.HoTen, n.NgaySinh, v.DiaChi, v.SoDienThoai, "
                "       v.ViTri, v.TenDV, v.Bac, v.SoNgayCong, v.HeSoViTri, "
                "       v.LuongTheoViTri, v.HoaHong, v.TongLuong "
                "FROM V_BANG_LUONG v JOIN NHANVIEN_TOANHA n ON n.MaNV = v.MaNV "
                "WHERE v.Thang = %s AND v.Nam = %s "
                "  AND (v.MaNV LIKE %s OR v.HoTen LIKE %s) "
                "ORDER BY v.TongLuong DESC",
                (thang, nam, f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được bảng lương: ' + str(e), 'danger')

    tong = sum(r['TongLuong'] or 0 for r in ds)
    return render_template('luong.html', ds=ds, thang=thang, nam=nam,
                           tong=tong, tu_khoa=tu_khoa)