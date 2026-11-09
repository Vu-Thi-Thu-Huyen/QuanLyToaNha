from flask import Blueprint, render_template, flash
from mysql.connector import Error
from auth import login_required
from db import get_connection

thongke_bp = Blueprint('thongke', __name__, url_prefix='/thongke')

# Số bản ghi TỐI THIỂU của từng bảng (số tạm, sửa theo yêu cầu của thầy/cô)
YEU_CAU_BAN_GHI = {
    'CONGTY': 10,
    'NHANVIEN_CONGTY': 30,
    'THE_RA_VAO': 30,
    'LICHSU_RA_VAO': 100,
    'DICHVU': 5,
    'SUDUNGDICHVU': 20,
    'NHANVIEN_TOANHA': 10,
    'PHANCONG': 10,
    'TAIKHOAN': 1,
}


def thong_ke_ban_ghi():
    ket_qua = []
    conn = get_connection()
    try:
        cur = conn.cursor()
        for bang, toi_thieu in YEU_CAU_BAN_GHI.items():
            dong = {'bang': bang, 'toi_thieu': toi_thieu, 'so_luong': None}
            try:
                cur.execute(f"SELECT COUNT(*) FROM `{bang}`")
                dong['so_luong'] = cur.fetchone()[0]
                dong['trang_thai'] = 'dat' if dong['so_luong'] >= toi_thieu else 'chua_dat'
            except Error as e:
                dong['trang_thai'] = 'chua_co_bang' if e.errno == 1146 else 'loi'
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
    so_dat = sum(1 for d in ds if d['trang_thai'] == 'dat')
    return render_template('thongke.html', ds=ds, so_dat=so_dat, tong=len(ds))