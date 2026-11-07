from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config

from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

from auth import login_required

from routes.congty import congty_bp

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(congty_bp)

# Đưa tên người dùng vào mọi template (kể cả template của các Blueprint)
@app.context_processor
def inject_user():
    return {'username': session.get('username')}

def lay_tai_khoan(ten_dang_nhap):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM TAIKHOAN WHERE ten_dang_nhap = %s", (ten_dang_nhap,))
        return cur.fetchone()
    finally:
        conn.close()


# Trang đăng nhập
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        try:
            tk = lay_tai_khoan(username)
        except Exception:
            flash('Không kết nối được cơ sở dữ liệu!')
            return render_template('login.html')

        if tk is None or not check_password_hash(tk['mat_khau_hash'], password):
            flash('Tên đăng nhập hoặc mật khẩu không đúng!')
        elif not tk['trang_thai']:
            flash('Tài khoản đã bị khóa!')
        else:
            session['username'] = tk['ten_dang_nhap']
            session['vai_tro'] = tk['vai_tro']
            return redirect(url_for('dashboard'))

    return render_template('login.html')


# Trang chu Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# Dang xuat
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


def tao_admin_mac_dinh():
    # Nếu bảng TAIKHOAN còn trống thì tự tạo tài khoản admin / 123456
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM TAIKHOAN")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO TAIKHOAN (ten_dang_nhap, mat_khau_hash, vai_tro) "
                "VALUES (%s, %s, 'admin')",
                ('admin', generate_password_hash('123456')),
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print("Chua tao duoc tai khoan admin mac dinh:", e)


if __name__ == '__main__':
    tao_admin_mac_dinh()
    app.run(debug=True)