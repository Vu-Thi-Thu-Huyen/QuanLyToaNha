from datetime import date, datetime
from flask import Blueprint, render_template, flash, request
from auth import login_required
from db import get_connection

ravao_bp = Blueprint('ravao', __name__, url_prefix='/ravao')


@ravao_bp.route('/')
@login_required
def theo_ngay():
    tu_khoa = request.args.get('q', '').strip()
    ngay_str = request.args.get('ngay') or date.today().strftime('%Y-%m-%d')
    try:
        ngay = datetime.strptime(ngay_str, '%Y-%m-%d').date()
    except ValueError:
        ngay = date.today()
        ngay_str = ngay.strftime('%Y-%m-%d')

    ds = []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.callproc('PR_RAVAO_NGAY', [ngay])
            for res in cur.stored_results():
                cols = res.column_names
                ds = [dict(zip(cols, row)) for row in res.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được dữ liệu ra/vào: ' + str(e), 'danger')

    if tu_khoa:
        kw = tu_khoa.lower()
        ds = [r for r in ds
              if kw in str(r.get('MaNV', '')).lower()
              or kw in str(r.get('HoTen', '')).lower()]

    return render_template('ravao.html', ds=ds, ngay=ngay_str, tu_khoa=tu_khoa)