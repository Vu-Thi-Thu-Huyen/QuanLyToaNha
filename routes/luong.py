import re
from datetime import date, timedelta
from flask import Blueprint, render_template, flash, request, redirect, url_for
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
    ten_nhan_vien = []

    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            # Lấy danh sách tên nhân viên
            cur.execute(
                "SELECT DISTINCT n.HoTen FROM NHANVIEN_TOANHA n "
                "JOIN PHANCONG p ON p.MaNV = n.MaNV ORDER BY n.HoTen"
            )
            ten_nhan_vien = [
                row['HoTen'] for row in cur.fetchall()
            ]

            # Lấy bảng lương
            cur.execute(
                "SELECT v.MaNV, v.HoTen, n.CCCD, n.GioiTinh, n.NgaySinh, v.DiaChi, "
                "v.SoDienThoai, v.ViTri, v.TenDV, v.Bac, "
                "v.SoNgayCong, v.HeSoViTri, v.LuongTheoViTri, "
                "v.DoanhThuDV, v.HoaHong, v.TongLuong "
                "FROM V_BANG_LUONG v "
                "JOIN NHANVIEN_TOANHA n ON n.MaNV = v.MaNV "
                "WHERE v.Thang = %s AND v.Nam = %s "
                "AND (v.MaNV LIKE %s OR v.HoTen LIKE %s) "
                "ORDER BY v.TongLuong DESC",
                (thang, nam, f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()
            print('DEBUG:', ds[0] if ds else 'rong')

        finally:
            conn.close()

    except Exception as e:
        flash('Không đọc được bảng lương: ' + str(e), 'danger')

    tong = sum(r['TongLuong'] or 0 for r in ds)

    return render_template(
        'luong.html',
        tab='bang_luong',
        ds=ds,
        thang=thang,
        nam=nam,
        tong=tong,
        tu_khoa=tu_khoa,
        ten_nhan_vien=ten_nhan_vien
    )


def tinh_so_ngay_cong(ngay_bat_dau):
    """Đếm số ngày làm việc từ ngày bắt đầu đến hết tháng (bỏ Chủ nhật)."""
    if ngay_bat_dau.month == 12:
        dau_thang_sau = date(ngay_bat_dau.year + 1, 1, 1)
    else:
        dau_thang_sau = date(ngay_bat_dau.year, ngay_bat_dau.month + 1, 1)

    so_ngay = 0
    d = ngay_bat_dau
    while d < dau_thang_sau:
        if d.weekday() != 6:  # 6 = Chủ nhật
            so_ngay += 1
        d += timedelta(days=1)
    return so_ngay


def lay_danh_muc():
    """Lấy nhân viên, dịch vụ, vị trí, bậc lương để đổ vào form/bảng."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT MaNV, HoTen FROM NHANVIEN_TOANHA ORDER BY MaNV")
        nhan_vien = cur.fetchall()
        cur.execute("SELECT MaDV, TenDV FROM DICHVU ORDER BY MaDV")
        dich_vu = cur.fetchall()
        cur.execute(
            "SELECT MaViTri, MaDV, TenViTri, HeSo "
            "FROM VITRI_DICHVU ORDER BY TenViTri"
        )
        vi_tri = cur.fetchall()
        cur.execute(
            "SELECT Bac, LuongCoBan, TyLeHoaHong FROM bac_luong ORDER BY Bac"
        )
        bac_luong = cur.fetchall()
        return nhan_vien, dich_vu, vi_tri, bac_luong
    finally:
        conn.close()

def dem_nguoi_theo_dv(thang, nam):
    """Đếm số nhân viên đang được phân công trong mỗi dịch vụ ở tháng đó.
    Khóa None là nhóm hành chính (không thuộc dịch vụ)."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT MaDV, COUNT(DISTINCT MaNV) AS so_nguoi "
            "FROM PHANCONG WHERE Thang = %s AND Nam = %s "
            "GROUP BY MaDV",
            (thang, nam)
        )
        return {r['MaDV']: r['so_nguoi'] for r in cur.fetchall()}
    finally:
        conn.close()


def tao_ma_nv(cur):
    """Trả về mã NVT nhỏ nhất chưa dùng: ưu tiên mã bị trống ở giữa, hết chỗ trống mới lấy mã mới."""
    cur.execute("SELECT MaNV FROM NHANVIEN_TOANHA WHERE MaNV LIKE 'NVT%'")
    da_dung = set()
    for r in cur.fetchall():
        phan_so = r['MaNV'][3:]
        if phan_so.isdigit():
            da_dung.add(int(phan_so))

    so = 1
    while so in da_dung:
        so += 1
    return f'NVT{so:02d}'


def kiem_tra_vi_tri(cur, ma_vi_tri, ma_dv):
    """Trả về dòng vị trí nếu vị trí thuộc đúng dịch vụ, ngược lại None."""
    cur.execute(
        "SELECT TenViTri, HeSo, MaDV FROM VITRI_DICHVU WHERE MaViTri = %s",
        (ma_vi_tri,)
    )
    vt = cur.fetchone()
    if not vt or vt['MaDV'] != ma_dv:
        return None
    return vt


# ---------- Trang 2: Đăng ký ----------
@luong_bp.route('/dang-ky', methods=['GET', 'POST'])
@login_required
def dang_ky():
    nhan_vien, dich_vu, vi_tri, bac_luong = [], [], [], []
    form = {}

    try:
        nhan_vien, dich_vu, vi_tri, bac_luong = lay_danh_muc()
    except Exception as e:
        flash('Không đọc được danh mục: ' + str(e), 'danger')

    if request.method == 'POST':
        form = request.form
        ho_ten = form.get('ho_ten', '').strip()
        cccd = form.get('cccd', '').strip()
        gioi_tinh = form.get('gioi_tinh', '').strip()
        ngay_sinh = form.get('ngay_sinh', '').strip()
        dia_chi = form.get('dia_chi', '').strip()
        sdt = form.get('so_dien_thoai', '').strip()
        ma_vi_tri = form.get('ma_vi_tri', '').strip()
        ma_dv = form.get('ma_dv', '').strip() or None

        try:
            bac = int(form.get('bac', ''))
            ngay_bd = date.fromisoformat(form.get('ngay_bat_dau', ''))
            if bac not in [b['Bac'] for b in bac_luong]:
                raise ValueError
        except ValueError:
            flash('Bậc hoặc ngày bắt đầu không hợp lệ.', 'danger')
            return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)

        if not (ho_ten and cccd and gioi_tinh and ngay_sinh and dia_chi and sdt):
            flash('Cần nhập đủ họ tên, CCCD, giới tính, ngày sinh, '
                  'địa chỉ và số điện thoại.', 'danger')
            return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)

        if not (cccd.isdigit() and len(cccd) == 12):
            flash('CCCD phải gồm đúng 12 chữ số.', 'danger')
            return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)

        thang, nam = ngay_bd.month, ngay_bd.year
        so_ngay_cong = tinh_so_ngay_cong(ngay_bd)

        try:
            conn = get_connection()
            try:
                cur = conn.cursor(dictionary=True)

                vt = kiem_tra_vi_tri(cur, ma_vi_tri, ma_dv)
                if not vt:
                    flash('Vị trí không thuộc dịch vụ đã chọn.', 'danger')
                    return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)

                cur.execute("SELECT MaNV, HoTen FROM NHANVIEN_TOANHA WHERE CCCD = %s",
                            (cccd,))
                trung = cur.fetchone()

                # Số điện thoại không được trùng với nhân viên khác
                cur.execute(
                    "SELECT MaNV, HoTen FROM NHANVIEN_TOANHA "
                    "WHERE SoDienThoai = %s AND MaNV <> %s",
                    (sdt, trung['MaNV'] if trung else '')
                )
                trung_sdt = cur.fetchone()
                if trung_sdt:
                    flash(f'Số điện thoại này đã thuộc về {trung_sdt["HoTen"]} '
                          f'({trung_sdt["MaNV"]}).', 'danger')
                    return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)
                if trung:
                    cur.execute("SELECT 1 FROM PHANCONG WHERE MaNV = %s LIMIT 1",
                                (trung['MaNV'],))
                    if cur.fetchone():
                        flash(f'CCCD này đã thuộc về {trung["HoTen"]} ({trung["MaNV"]}).',
                              'danger')
                        return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)

                    # Hồ sơ cũ không còn phân công: dùng lại, KHÔNG insert nữa
                    ma_nv = trung['MaNV']
                    cur.execute(
                        "UPDATE NHANVIEN_TOANHA SET HoTen = %s, GioiTinh = %s, "
                        "NgaySinh = %s, DiaChi = %s, SoDienThoai = %s "
                        "WHERE MaNV = %s",
                        (ho_ten, gioi_tinh, ngay_sinh, dia_chi, sdt, ma_nv)
                    )
                else:
                    ma_nv = tao_ma_nv(cur)
                    cur.execute(
                        "INSERT INTO NHANVIEN_TOANHA "
                        "(MaNV, HoTen, CCCD, GioiTinh, NgaySinh, DiaChi, SoDienThoai) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (ma_nv, ho_ten, cccd, gioi_tinh, ngay_sinh, dia_chi, sdt)
                    )

                cur.execute(
                    "INSERT INTO PHANCONG "
                    "(MaNV, MaDV, ViTri, Bac, Thang, Nam, HeSoViTri, SoNgayCong) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (ma_nv, ma_dv, vt['TenViTri'], bac, thang, nam,
                     vt['HeSo'], so_ngay_cong)
                )
                conn.commit()
                flash(f'Đã đăng ký {ho_ten} ({ma_nv}) làm "{vt["TenViTri"]}" '
                      f'({so_ngay_cong} ngày công).', 'success')
                return redirect(url_for('luong.danh_sach', thang=thang, nam=nam))
            finally:
                conn.close()
        except Exception as e:
            flash('Không lưu được phân công: ' + str(e), 'danger')

    return hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong)


# ---------- Trang 3: Danh sách + sửa/xóa ----------
def hien_form_dang_ky(form, nhan_vien, dich_vu, vi_tri, bac_luong):
    hom_nay = date.today()
    try:
        so_nguoi = dem_nguoi_theo_dv(hom_nay.month, hom_nay.year)
    except Exception:
        so_nguoi = {}
    return render_template('dang_ky.html', tab='dang_ky',
                           nhan_vien=nhan_vien, dich_vu=dich_vu,
                           vi_tri=vi_tri, bac_luong=bac_luong,
                           so_nguoi=so_nguoi, form=form, hom_nay=hom_nay)


@luong_bp.route('/danh-sach')
@login_required
def danh_sach():
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

    ds, dich_vu, vi_tri, bac_luong = [], [], [], []
    ten_nhan_vien = []  # MỚI
    try:
        _, dich_vu, vi_tri, bac_luong = lay_danh_muc()
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            # MỚI: lấy danh sách tên để gợi ý ở ô tìm kiếm (giống trang Bảng lương)
            cur.execute(
                "SELECT DISTINCT n.HoTen FROM NHANVIEN_TOANHA n "
                "JOIN PHANCONG p ON p.MaNV = n.MaNV ORDER BY n.HoTen"
            )
            ten_nhan_vien = [row['HoTen'] for row in cur.fetchall()]

            cur.execute(
                "SELECT p.MaNV, n.HoTen, p.MaDV, d.TenDV, p.ViTri, p.Bac, "
                "p.Thang, p.Nam, p.HeSoViTri, p.SoNgayCong, "
                "b.LuongCoBan, b.TyLeHoaHong "
                "FROM PHANCONG p "
                "JOIN NHANVIEN_TOANHA n ON n.MaNV = p.MaNV "
                "LEFT JOIN DICHVU d ON d.MaDV = p.MaDV "
                "LEFT JOIN bac_luong b ON b.Bac = p.Bac "
                "WHERE p.Thang = %s AND p.Nam = %s "
                "AND (p.MaNV LIKE %s OR n.HoTen LIKE %s) "
                "ORDER BY p.MaNV",
                (thang, nam, f"%{tu_khoa}%", f"%{tu_khoa}%")
            )
            ds = cur.fetchall()
        finally:
            conn.close()
    except Exception as e:
        flash('Không đọc được danh sách: ' + str(e), 'danger')

    return render_template('danh_sach.html', tab='danh_sach', ds=ds,
                           dich_vu=dich_vu, vi_tri=vi_tri,
                           bac_luong=bac_luong, thang=thang, nam=nam,
                           tu_khoa=tu_khoa,
                           ten_nhan_vien=ten_nhan_vien)  # MỚI

@luong_bp.route('/sua/<ma_nv>/<int:thang>/<int:nam>', methods=['POST'])
@login_required
def sua(ma_nv, thang, nam):
    ma_dv = request.form.get('ma_dv', '').strip() or None
    ma_vi_tri = request.form.get('ma_vi_tri', '').strip()

    try:
        bac = int(request.form.get('bac', ''))
        so_ngay_cong = int(request.form.get('so_ngay_cong', ''))
        if bac < 1 or not 0 <= so_ngay_cong <= 31:
            raise ValueError
    except ValueError:
        flash('Bậc hoặc ngày công không hợp lệ.', 'danger')
        return redirect(url_for('luong.danh_sach', thang=thang, nam=nam))

    try:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)

            cur.execute("SELECT 1 FROM bac_luong WHERE Bac = %s", (bac,))
            if not cur.fetchone():
                flash('Bậc lương không tồn tại.', 'danger')
                return redirect(url_for('luong.danh_sach', thang=thang, nam=nam))

            vt = kiem_tra_vi_tri(cur, ma_vi_tri, ma_dv)
            if not vt:
                flash('Vị trí không thuộc dịch vụ đã chọn.', 'danger')
            else:
                cur.execute(
                    "UPDATE PHANCONG SET MaDV = %s, ViTri = %s, Bac = %s, "
                    "HeSoViTri = %s, SoNgayCong = %s "
                    "WHERE MaNV = %s AND Thang = %s AND Nam = %s",
                    (ma_dv, vt['TenViTri'], bac, vt['HeSo'],
                     so_ngay_cong, ma_nv, thang, nam)
                )
                conn.commit()
                flash(f'Đã cập nhật phân công của {ma_nv}.', 'success')
        finally:
            conn.close()
    except Exception as e:
        flash('Không sửa được: ' + str(e), 'danger')

    return redirect(url_for('luong.danh_sach', thang=thang, nam=nam))


@luong_bp.route('/xoa/<ma_nv>/<int:thang>/<int:nam>', methods=['POST'])
@login_required
def xoa(ma_nv, thang, nam):
    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM PHANCONG "
                "WHERE MaNV = %s AND Thang = %s AND Nam = %s",
                (ma_nv, thang, nam)
            )
            cur.execute("SELECT COUNT(*) FROM PHANCONG WHERE MaNV = %s", (ma_nv,))
            con_lai = cur.fetchone()[0]

            thong_bao = f'Đã xóa phân công của {ma_nv} ({thang}/{nam}).'
            if con_lai == 0:
                try:
                    cur.execute("DELETE FROM NHANVIEN_TOANHA WHERE MaNV = %s",
                                (ma_nv,))
                    thong_bao = f'Đã xóa nhân viên {ma_nv} và phân công của họ.'
                except Exception as e:
                    if getattr(e, 'errno', None) == 1062 and 'SoDienThoai' in str(e):
                        flash('Số điện thoại này đã tồn tại.', 'danger')
                    else:
                        flash('Không lưu được phân công: ' + str(e), 'danger')
            conn.commit()
            flash(thong_bao, 'success')
        finally:
            conn.close()
    except Exception as e:
        flash('Không xóa được: ' + str(e), 'danger')

    return redirect(url_for('luong.danh_sach', thang=thang, nam=nam))