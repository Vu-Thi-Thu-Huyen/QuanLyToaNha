from flask import Blueprint, render_template, flash
from auth import login_required
from db import get_connection

congty_bp = Blueprint('congty', __name__, url_prefix='/congty')


@congty_bp.route('/')
@login_required
def danh_sach():
    ds = []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT MaCT, TenCT FROM CONGTY ORDER BY MaCT")
            ds = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Chưa đọc được bảng CONGTY: ' + str(e), 'danger')
    return render_template('congty.html', ds=ds)