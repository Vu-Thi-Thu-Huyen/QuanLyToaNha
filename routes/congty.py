from flask import Blueprint, render_template, flash, request
from auth import login_required
from db import get_connection

congty_bp = Blueprint('congty', __name__, url_prefix='/congty')


@congty_bp.route('/')
@login_required
def danh_sach():
    tu_khoa = request.args.get('q', '').strip()
    ds = []
    ten_cong_ty = []

    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            cur.execute(
                "SELECT DISTINCT TenCT FROM V_TONG_CHIPHI_CONGTY "
                "ORDER BY TenCT ASC"
            )
            ten_cong_ty = [row['TenCT'] for row in cur.fetchall()]

            cur.execute(
                "SELECT MaCT, TenCT, MaSoThue, VonDieuLe, LinhVuc, "
                "SoNhanVien, DiaChi, SoDienThoai, DienTichThue, "
                "TienThue, TienDichVu, TongChiPhi "
                "FROM V_TONG_CHIPHI_CONGTY "
                "WHERE MaCT LIKE %s OR TenCT LIKE %s "
                "ORDER BY TongChiPhi DESC",
                (f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()

            if tu_khoa:
                ds = [
                    ct for ct in ds
                    if tu_khoa.lower() in str(ct['MaCT']).lower()
                    or tu_khoa.lower() in str(ct['TenCT']).lower()
                ]

        finally:
            conn.close()

    except Exception as e:
        flash('Không đọc được dữ liệu công ty: ' + str(e), 'danger')

    return render_template(
        'congty.html',
        ds=ds,
        tu_khoa=tu_khoa,
        ten_cong_ty=ten_cong_ty
    )
