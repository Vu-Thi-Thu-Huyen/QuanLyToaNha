import re
from datetime import date, datetime
from flask import Blueprint, render_template, flash, request, redirect, url_for
from helpers import lay_nhieu, thuc_thi
from auth import login_required
from db import get_connection

ravao_bp = Blueprint('ravao', __name__, url_prefix='/ravao')

NHAN_VI_TRI = {
    'TANG_1': 'Tầng 1',
    'B1': 'Hầm B1',
    'B2': 'Hầm B2',
    'CHUA_RA_VAO': 'Chưa ra vào',
}
VI_TRI = ['TANG_1', 'B1', 'B2']


# ---------------------------------------------------------------- TAB 1: LƯỢT RA VÀO
@ravao_bp.route('/')
@login_required
def theo_ngay():
    tu_khoa = request.args.get('q', '').strip()
    vt = request.args.get('vt', '').strip()
    ct = request.args.get('ct', '').strip()
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

    ds_vitri = sorted({r['ViTri'] for r in ds if r.get('ViTri')})
    ds_ct = sorted({r['TenCT'] for r in ds if r.get('TenCT')})
    if vt not in ds_vitri:
        vt = ''
    if ct not in ds_ct:
        ct = ''

    if tu_khoa:
        kw = tu_khoa.lower()
        ds = [r for r in ds
              if kw in str(r.get('MaNV', '')).lower()
              or kw in str(r.get('HoTen', '')).lower()
              or kw in str(r.get('MaThe') or '').lower()]
    if ct:
        ds = [r for r in ds if r.get('TenCT') == ct]
    if vt:
        ds = [r for r in ds if r.get('ViTri') == vt]
    return render_template('ravao.html', ds=ds, ngay=ngay_str, tu_khoa=tu_khoa,
                           vt=vt, ds_vitri=ds_vitri, ct=ct, ds_ct=ds_ct,
                           nhan_vi_tri=NHAN_VI_TRI)


# ---------------------------------------------------------------- TAB 2: CẤP THẺ
@ravao_bp.route('/the')
@login_required
def cap_the():
    ds_nv, ds_the, ds_ct = [], [], []
    try:
        ds_ct = lay_nhieu(
            "SELECT MaCT, TenCT, ChoPhep, HienCo, ConTrong "
            "FROM V_SO_NHANVIEN_CONGTY ORDER BY TenCT")
        ds_nv = lay_nhieu(
            "SELECT n.MaNV, n.HoTen, c.TenCT FROM NHANVIEN_CONGTY n "
            "JOIN CONGTY c ON c.MaCT = n.MaCT "
            "WHERE n.MaNV NOT IN (SELECT MaNV FROM THE_RA_VAO "
            "  WHERE TrangThai = 'HOAT_DONG' "
            "  AND (NgayHetHan IS NULL OR NgayHetHan >= CURDATE())) "
            "ORDER BY c.TenCT, n.HoTen")
        ds_the = lay_nhieu(
            "SELECT t.MaThe, n.MaNV, n.HoTen, c.TenCT, t.NgayCap, t.TrangThai "
            "FROM THE_RA_VAO t JOIN NHANVIEN_CONGTY n ON n.MaNV = t.MaNV "
            "JOIN CONGTY c ON c.MaCT = n.MaCT ORDER BY t.MaThe DESC")
    except Exception as e:
        flash('Không đọc được dữ liệu thẻ: ' + str(e), 'danger')
    return render_template('ravao_cap_the.html', ds_nv=ds_nv, ds_the=ds_the, ds_ct=ds_ct,
                           hom_nay=date.today().strftime('%Y-%m-%d'))


@ravao_bp.route('/the/cap', methods=['POST'])
@login_required
def cap_the_moi():
    f = request.form
    che_do = f.get('che_do', 'moi')
    ngay = f.get('ngay', '').strip()
    loi = []

    try:
        datetime.strptime(ngay, '%Y-%m-%d')
    except ValueError:
        loi.append('Ngày cấp không hợp lệ.')

    ma_nv = ''
    ma_ct = ho_ten = cccd = ngay_sinh = gioi_tinh = sdt = chuc_vu = None
    if che_do == 'cu':
        ma_nv = f.get('nv', '').split(' - ')[0].strip()
        if not ma_nv:
            loi.append('Vui lòng chọn nhân viên.')
    else:
        ma_ct = f.get('ma_ct', '').strip()
        ho_ten = f.get('ho_ten', '').strip()
        cccd = f.get('cccd', '').strip()
        ngay_sinh = f.get('ngay_sinh', '').strip() or None
        gioi_tinh = f.get('gioi_tinh', '').strip() or None
        sdt = f.get('sdt', '').strip() or None
        chuc_vu = f.get('chuc_vu', '').strip() or None
        if not ma_ct:
            loi.append('Vui lòng chọn công ty.')
        if not ho_ten:
            loi.append('Họ tên không được để trống.')
        if not re.fullmatch(r'[0-9]{12}', cccd):
            loi.append('CCCD phải gồm đúng 12 chữ số.')
        if gioi_tinh not in (None, 'Nam', 'Nu'):
            loi.append('Giới tính không hợp lệ.')
        if sdt and not re.fullmatch(r'[0-9]{9,11}', sdt):
            loi.append('Số điện thoại phải gồm 9-11 chữ số.')
        if ngay_sinh:
            try:
                if datetime.strptime(ngay_sinh, '%Y-%m-%d').date() >= date.today():
                    loi.append('Ngày sinh phải nhỏ hơn hôm nay.')
            except ValueError:
                loi.append('Ngày sinh không hợp lệ.')

    if loi:
        for m in loi:
            flash(m, 'danger')
        return redirect(url_for('ravao.cap_the'))

    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            if che_do != 'cu':
                cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(MaNV, 3) AS UNSIGNED)), 0) + 1 "
                            "FROM NHANVIEN_CONGTY")
                ma_nv = 'NV%02d' % cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO NHANVIEN_CONGTY "
                    "(MaNV, MaCT, HoTen, CCCD, NgaySinh, GioiTinh, SoDienThoai, ChucVu) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (ma_nv, ma_ct, ho_ten, cccd, ngay_sinh, gioi_tinh, sdt, chuc_vu))

            cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(MaThe, 4) AS UNSIGNED)), 0) + 1 "
                        "FROM THE_RA_VAO")
            ma_the = 'THE%02d' % cur.fetchone()[0]
            cur.execute(
                "INSERT INTO THE_RA_VAO (MaThe, MaNV, NgayCap, NgayHetHan) "
                "VALUES (%s, %s, %s, DATE_ADD(%s, INTERVAL 1 YEAR))",
                (ma_the, ma_nv, ngay, ngay))
            conn.commit()
            flash(f'Đã cấp thẻ {ma_the} cho nhân viên {ma_nv}.', 'success')
        except Exception as e:
            conn.rollback()
            if '1062' in str(e):
                flash('CCCD này đã được đăng ký cho một nhân viên khác.', 'danger')
            else:
                flash(str(e), 'danger')
        finally:
            conn.close()
    except Exception as e:
        flash('Không kết nối được cơ sở dữ liệu: ' + str(e), 'danger')
    return redirect(url_for('ravao.cap_the'))


@ravao_bp.route('/the/<string:ma_the>/thuhoi', methods=['POST'])
@login_required
def thu_hoi_the(ma_the):
    ok, kq = thuc_thi("UPDATE THE_RA_VAO SET TrangThai = 'BI_KHOA' WHERE MaThe = %s", (ma_the,))
    flash('Đã thu hồi thẻ.' if ok else kq, 'success' if ok else 'danger')
    return redirect(url_for('ravao.cap_the'))


# ---------------------------------------------------------------- TAB 3: GHI NHẬN
@ravao_bp.route('/ghi-nhan')
@login_required
def ghi_nhan():
    ds_the, gan_day = [], []
    try:
        ds_the = lay_nhieu(
            "SELECT t.MaThe, n.HoTen, c.TenCT FROM THE_RA_VAO t "
            "JOIN NHANVIEN_CONGTY n ON n.MaNV = t.MaNV JOIN CONGTY c ON c.MaCT = n.MaCT "
            "WHERE t.TrangThai = 'HOAT_DONG' "
            "AND (t.NgayHetHan IS NULL OR t.NgayHetHan >= CURDATE()) ORDER BY n.HoTen")
        gan_day = lay_nhieu(
            "SELECT l.ThoiGian, n.HoTen, l.ViTri, l.HanhDong AS Chieu FROM LICHSU_RA_VAO l "
            "JOIN THE_RA_VAO t ON t.MaThe = l.MaThe JOIN NHANVIEN_CONGTY n ON n.MaNV = t.MaNV "
            "ORDER BY l.ThoiGian DESC LIMIT 10")
    except Exception as e:
        flash('Không đọc được dữ liệu: ' + str(e), 'danger')
    return render_template('ravao_ghi_nhan.html', ds_the=ds_the, gan_day=gan_day,
                           vi_tri=VI_TRI, nhan_vi_tri=NHAN_VI_TRI,
                           bay_gio=datetime.now().strftime('%Y-%m-%dT%H:%M'))


@ravao_bp.route('/ghi-nhan', methods=['POST'])
@login_required
def them_luot():
    ma_the = request.form.get('ma_the', '').strip()
    vi_tri = request.form.get('vi_tri', '').strip()
    chieu = request.form.get('chieu', '').strip()
    tg = request.form.get('thoi_gian', '').strip()
    try:
        tg_sql = datetime.strptime(tg, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:00')
    except ValueError:
        tg_sql = None

    if not ma_the or vi_tri not in VI_TRI or chieu not in ('VAO', 'RA') or not tg_sql:
        flash('Vui lòng chọn đủ thẻ, vị trí, chiều và thời gian hợp lệ.', 'danger')
    else:
        ok, kq = thuc_thi(
            "INSERT INTO LICHSU_RA_VAO (MaThe, ViTri, HanhDong, ThoiGian) VALUES (%s, %s, %s, %s)",
            (ma_the, vi_tri, chieu, tg_sql))
        flash('Đã ghi nhận lượt ra/vào.' if ok else kq, 'success' if ok else 'danger')
    return redirect(url_for('ravao.ghi_nhan'))