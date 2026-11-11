from flask import Blueprint, render_template, flash
from auth import login_required
from db import get_connection

baocao_bp = Blueprint('baocao', __name__, url_prefix='/baocao')


@baocao_bp.route('/')
@login_required
def bao_cao():
    so_nv, thieu_dv, chua_the = [], [], []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT * FROM V_SO_NHANVIEN_CONGTY ORDER BY MaCT")
            so_nv = cur.fetchall()

            cur.execute("SELECT * FROM V_CONGTY_THIEU_DV_BATBUOC")
            thieu_dv = cur.fetchall()

            cur.execute("SELECT * FROM V_NV_CHUA_CO_THE")
            chua_the = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được báo cáo: ' + str(e), 'danger')

    return render_template('baocao.html',
                           so_nv=so_nv, thieu_dv=thieu_dv, chua_the=chua_the)