import math
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (Blueprint, render_template, flash, request,
                   redirect, url_for, abort)
from auth import login_required
from db import get_connection
from helpers import lay_mot, thuc_thi

congty_bp = Blueprint('congty', __name__, url_prefix='/congty')


# ---------------------------------------------------------------- DANH SÁCH
@congty_bp.route('/')
@login_required
def danh_sach():
    tu_khoa = request.args.get('q', '').strip()
    hom_nay = date.today()
    try:
        thang = int(request.args.get('thang', hom_nay.month))
        nam = int(request.args.get('nam', hom_nay.year))
        if not (1 <= thang <= 12 and 2000 <= nam <= 2100):
            raise ValueError
    except ValueError:
        thang, nam = hom_nay.month, hom_nay.year

    ds = []
    ten_cong_ty = []

    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT DISTINCT TenCT FROM CONGTY ORDER BY TenCT ASC")
            ten_cong_ty = [row['TenCT'] for row in cur.fetchall()]

            cur.execute(
                "SELECT t.*, t.TienThue + t.TienDichVu AS TongChiPhi FROM ("
                "  SELECT c.MaCT, c.TenCT, c.MaSoThue, c.VonDieuLe, c.LinhVuc, "
                "         c.SoNhanVien, c.DiaChi, c.SoDienThoai, "
                "         COALESCE(p.DienTich, 0) AS DienTichThue, "
                "         ROUND(COALESCE(p.DienTich, 0) * FN_DONGIA_M2(), 0) AS TienThue, "
                "         FN_TONG_TIEN_DV_CONGTY(c.MaCT, %s, %s) AS TienDichVu "
                "  FROM CONGTY c LEFT JOIN PHONG p ON p.MaPhong = c.MaPhong "
                "  WHERE c.MaCT LIKE %s OR c.TenCT LIKE %s"
                ") t ORDER BY TongChiPhi DESC",
                (thang, nam, f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()
        finally:
            conn.close()

    except Exception as e:
        flash('Không đọc được dữ liệu công ty: ' + str(e), 'danger')

    return render_template('congty.html', ds=ds, tu_khoa=tu_khoa,
                           ten_cong_ty=ten_cong_ty, tab='danh_sach',
                           thang=thang, nam=nam, nam_nay=hom_nay.year)


# ---------------------------------------------------------------- KIỂM TRA FORM
def _doc_so(form, truong, nhan, loi, kieu, duong=False):
    """Đọc một ô số. Sai thì thêm câu lỗi vào `loi` và trả về None."""
    raw = form.get(truong, '').strip()
    try:
        v = kieu(raw)
        if not math.isfinite(v):
            raise ValueError
    except (ValueError, InvalidOperation):
        loi.append(f'{nhan} phải là một số hợp lệ.')
        return None
    if duong and v <= 0:
        loi.append(f'{nhan} phải lớn hơn 0.')
        return None
    if v < 0:
        loi.append(f'{nhan} không được âm.')
        return None
    return v


def doc_form(form, la_sua):
    """Kiểm tra dữ liệu form công ty. Trả về (dict dữ liệu, danh sách lỗi)."""
    loi = []
    d = {k: form.get(k, '').strip()
         for k in ('MaCT', 'TenCT', 'MaSoThue', 'LinhVuc', 'SoDienThoai')}

    if not la_sua and not re.fullmatch(r'[A-Za-z0-9]{1,10}', d['MaCT']):
        loi.append('Mã công ty gồm 1-10 chữ cái hoặc chữ số.')
    for k, nhan in (('TenCT', 'Tên công ty'), ('LinhVuc', 'Lĩnh vực'),
                    ('SoDienThoai', 'Số điện thoại')):
        if not d[k]:
            loi.append(f'{nhan} không được để trống.')
    if not re.fullmatch(r'[0-9]{10}([0-9]{3})?', d['MaSoThue']):
        loi.append('Mã số thuế phải gồm 10 hoặc 13 chữ số.')

    d['VonDieuLe'] = _doc_so(form, 'VonDieuLe', 'Vốn điều lệ', loi, int)
    d['SoNhanVien'] = _doc_so(form, 'SoNhanVien', 'Số nhân viên', loi, int)

    # Phòng thuê: địa chỉ tự sinh từ phòng đã chọn
    d['MaPhong'] = form.get('MaPhong', '').strip()
    d['DiaChi'] = ''
    phong = lay_mot("SELECT MaPhong, Tang FROM PHONG WHERE MaPhong = %s",
                    (d['MaPhong'],))
    if not phong:
        loi.append('Hãy chọn phòng thuê.')
    else:
        d['DiaChi'] = f"Tầng {phong['Tang']}, phòng {phong['MaPhong']}"
    return d, loi

def kiem_tra_trung(form, ma_ct_hien_tai=None):
    """Trả về danh sách lỗi trùng. ma_ct_hien_tai chỉ truyền khi đang SỬA."""
    cac_cot = [
        ("MaCT", "Mã công ty"),
        ("MaSoThue", "Mã số thuế"),
        ("SoDienThoai", "Số điện thoại"),
        ("DiaChi", "Địa chỉ trong tòa nhà"),
    ]
    loi = []
    for cot, ten in cac_cot:
        gia_tri = form.get(cot, "").strip()
        if not gia_tri:
            continue
        if cot == "MaCT" and ma_ct_hien_tai:
            continue  # khi sửa, mã công ty không đổi nên khỏi kiểm tra

        sql = f"SELECT MaCT FROM CONGTY WHERE {cot} = %s"
        tham_so = [gia_tri]
        if ma_ct_hien_tai:
            sql += " AND MaCT <> %s"      # loại trừ chính công ty đang sửa
            tham_so.append(ma_ct_hien_tai)

        if lay_mot(sql, tham_so):
            loi.append(f"{ten} \"{gia_tri}\" đã tồn tại.")
    return loi


# ---------------------------------------------------------------- DỮ LIỆU PHÒNG
def lay_du_lieu_phong(ma_ct=''):
    """Dữ liệu cho ô đơn giá, ô danh sách phòng và ô chọn phòng."""
    bang_gia, tang_phong, da_thue, phong_chon = [], {}, {}, []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            # Ô 2: bảng giá (các tầng giống nhau nên lấy tầng thấp nhất)
            cur.execute(
                "SELECT RIGHT(MaPhong, 2) AS so, DienTich, "
                "FN_DONGIA_M2() AS DonGiaThue, "
                "ROUND(DienTich * FN_DONGIA_M2(), 0) AS TienThue "
                "FROM PHONG WHERE Tang = (SELECT MIN(Tang) FROM PHONG) "
                "ORDER BY MaPhong"
            )
            bang_gia = cur.fetchall()

            # Ô 3: toàn bộ phòng gom theo tầng
            cur.execute("SELECT MaPhong, Tang FROM PHONG ORDER BY Tang, MaPhong")
            for r in cur.fetchall():
                tang_phong.setdefault(r['Tang'], []).append(r['MaPhong'])

            # Phòng đã thuê (kèm tên công ty để hiện khi rê chuột)
            cur.execute("SELECT MaPhong, TenCT FROM CONGTY WHERE MaPhong IS NOT NULL")
            da_thue = {r['MaPhong']: r['TenCT'] for r in cur.fetchall()}

            # Ô chọn phòng: phòng chưa ai thuê, hoặc phòng của chính công ty đang sửa
            cur.execute(
                "SELECT MaPhong, Tang, DienTich, FN_DONGIA_M2() AS DonGiaThue FROM PHONG "
                "WHERE MaPhong NOT IN (SELECT MaPhong FROM CONGTY "
                "                      WHERE MaPhong IS NOT NULL AND MaCT <> %s) "
                "ORDER BY Tang, MaPhong",
                (ma_ct,)
            )
            phong_chon = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được danh sách phòng: ' + str(e), 'danger')
    return dict(bang_gia=bang_gia, tang_phong=tang_phong,
                phong_da_thue=da_thue, phong_chon=phong_chon)


# ---------------------------------------------------------------- THÊM
@congty_bp.route('/dang-ky', methods=['GET', 'POST'])
@login_required
def them():
    if request.method == 'GET':
        return render_template('congty_dang_ky.html', ct={}, tab='dang_ky',
                               **lay_du_lieu_phong())

    d, loi = doc_form(request.form, la_sua=False)
    if not loi:
        loi = kiem_tra_trung(request.form)
    if not loi:
        ok, kq = thuc_thi(
            "INSERT INTO CONGTY (MaCT, TenCT, MaSoThue, VonDieuLe, LinhVuc, "
            "SoNhanVien, DiaChi, MaPhong, SoDienThoai) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d['MaCT'], d['TenCT'], d['MaSoThue'], d['VonDieuLe'], d['LinhVuc'],
             d['SoNhanVien'], d['DiaChi'], d['MaPhong'], d['SoDienThoai']))
        if ok:
            flash(f"Đã thêm công ty {d['MaCT']}. Nhớ đăng ký dịch vụ bắt buộc "
                  "(Vệ sinh, Bảo vệ) cho công ty này.", 'success')
            return redirect(url_for('congty.danh_sach'))
        loi = [kq]

    for m in loi:
        flash(m, 'danger')
    # trả lại đúng những gì người dùng đã gõ, không bắt nhập lại từ đầu
    return render_template('congty_dang_ky.html', ct=request.form, tab='dang_ky',
                           **lay_du_lieu_phong())

# ---------------------------------------------------------------- SỬA
@congty_bp.route('/<ma_ct>/sua', methods=['GET', 'POST'])
@login_required
def sua(ma_ct):
    hien_tai = lay_mot("SELECT * FROM CONGTY WHERE MaCT = %s", (ma_ct,))
    if hien_tai is None:
        abort(404)

    if request.method == 'GET':
        return render_template('congty_form.html', ct=hien_tai, la_sua=True,
                               **lay_du_lieu_phong(ma_ct))

    form = request.form.copy()
    form['MaCT'] = ma_ct                       # khóa chính không cho đổi
    d, loi = doc_form(form, la_sua=True)
    if not loi:
        loi = kiem_tra_trung(d, ma_ct_hien_tai=ma_ct)
    if not loi:
        ok, kq = thuc_thi(
            "UPDATE CONGTY SET TenCT=%s, MaSoThue=%s, VonDieuLe=%s, LinhVuc=%s, "
            "SoNhanVien=%s, DiaChi=%s, MaPhong=%s, SoDienThoai=%s "
            "WHERE MaCT=%s",
            (d['TenCT'], d['MaSoThue'], d['VonDieuLe'], d['LinhVuc'],
             d['SoNhanVien'], d['DiaChi'], d['MaPhong'], d['SoDienThoai'], ma_ct))
        if ok:
            flash(f'Đã cập nhật công ty {ma_ct}.', 'success')
            return redirect(url_for('congty.danh_sach'))
        loi = [kq]

    for m in loi:
        flash(m, 'danger')
    return render_template('congty_form.html', ct=form, la_sua=True,
                           **lay_du_lieu_phong(ma_ct))

# ---------------------------------------------------------------- XÓA
@congty_bp.route('/<ma_ct>/xoa', methods=['POST'])
@login_required
def xoa(ma_ct):
    ok, kq = thuc_thi("DELETE FROM CONGTY WHERE MaCT = %s", (ma_ct,))
    if not ok:
        if '1451' in str(kq):
            flash(f'Không xóa được {ma_ct}: công ty còn dữ liệu liên quan '
                  '(ví dụ đăng ký dịch vụ). Hãy xóa các dữ liệu đó trước.', 'danger')
        else:
            flash(str(kq), 'danger')
    elif kq == 0:
        flash('Không tìm thấy công ty cần xóa.', 'warning')
    else:
        flash(f'Đã xóa công ty {ma_ct}.', 'success')
    return redirect(url_for('congty.quan_ly'))

# ---------------------------------------------------------------- TRANG 3: SỬA / XÓA
@congty_bp.route('/quan-ly')
@login_required
def quan_ly():
    tu_khoa = request.args.get('q', '').strip()
    ds, phongs = [], []
    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT c.MaCT, c.TenCT, c.MaSoThue, c.VonDieuLe, c.LinhVuc, "
                "c.SoNhanVien, c.SoDienThoai, c.MaPhong, p.DienTich, "
                "FN_DONGIA_M2() AS DonGiaThue, "
                "ROUND(p.DienTich * FN_DONGIA_M2(), 0) AS TienThue "
                "FROM CONGTY c LEFT JOIN PHONG p ON p.MaPhong = c.MaPhong "
                "WHERE c.MaCT LIKE %s OR c.TenCT LIKE %s ORDER BY c.MaCT",
                (f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()

            cur.execute(
                "SELECT p.MaPhong, p.Tang, p.DienTich, FN_DONGIA_M2() AS DonGiaThue, "
                "ROUND(p.DienTich * FN_DONGIA_M2(), 0) AS TienThue, c.MaCT AS chu "
                "FROM PHONG p LEFT JOIN CONGTY c ON c.MaPhong = p.MaPhong "
                "ORDER BY p.Tang, p.MaPhong"
            )
            phongs = [{'MaPhong': r['MaPhong'], 'Tang': r['Tang'],
                    'DienTich': int(r['DienTich']),
                    'DonGia': int(r['DonGiaThue']),
                    'TienThue': int(r['TienThue']), 'chu': r['chu']}
                    for r in cur.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được dữ liệu công ty: ' + str(e), 'danger')

    return render_template('congty_quan_ly.html', ds=ds, phongs=phongs,
                           tu_khoa=tu_khoa, tab='quan_ly')


@congty_bp.route('/<ma_ct>/cap-nhat', methods=['POST'])
@login_required
def cap_nhat(ma_ct):
    form = request.form.copy()
    form['MaCT'] = ma_ct
    d, loi = doc_form(form, la_sua=True)
    if not loi:
        loi = kiem_tra_trung(form, ma_ct_hien_tai=ma_ct)
    if not loi:
        ok, kq = thuc_thi(
            "UPDATE CONGTY SET TenCT=%s, MaSoThue=%s, VonDieuLe=%s, LinhVuc=%s, "
            "SoNhanVien=%s, DiaChi=%s, MaPhong=%s, SoDienThoai=%s "
            "WHERE MaCT=%s",
            (d['TenCT'], d['MaSoThue'], d['VonDieuLe'], d['LinhVuc'],
             d['SoNhanVien'], d['DiaChi'], d['MaPhong'], d['SoDienThoai'], ma_ct))
        if ok:
            flash(f'Đã cập nhật công ty {ma_ct}.', 'success')
            return redirect(url_for('congty.quan_ly', q=request.args.get('q', '')))
        loi = [kq]

    for m in loi:
        flash(f'{ma_ct}: {m}', 'danger')
    return redirect(url_for('congty.quan_ly', q=request.args.get('q', '')))
