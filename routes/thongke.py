from flask import Blueprint, render_template, flash
from mysql.connector import Error
from auth import login_required
from db import get_connection

thongke_bp = Blueprint('thongke', __name__, url_prefix='/thongke')

CAC_BANG = [
    'CONGTY', 'NHANVIEN_CONGTY', 'THE_RA_VAO', 'LICHSU_RA_VAO',
    'DICHVU', 'SUDUNGDICHVU', 'BAC_LUONG', 'NHANVIEN_TOANHA',
    'PHANCONG', 'TAIKHOAN',
]


def thong_ke_ban_ghi():
    ket_qua = []
    conn = get_connection()
    try:
        cur = conn.cursor()
        for bang in CAC_BANG:
            dong = {'bang': bang, 'so_luong': None}
            try:
                cur.execute(f"SELECT COUNT(*) FROM `{bang}`")
                dong['so_luong'] = cur.fetchone()[0]
            except Error:
                pass
            ket_qua.append(dong)
    finally:
        conn.close()
    return ket_qua


@thongke_bp.route('/')
@login_required
def trang_thong_ke():
    try:
        ds = thong_ke_ban_ghi()
    except Error as e:
        ds = []
        flash('Không kết nối được cơ sở dữ liệu: ' + str(e), 'danger')
    tong = sum(d['so_luong'] or 0 for d in ds)
    return render_template('thongke.html', ds=ds, tong=tong)