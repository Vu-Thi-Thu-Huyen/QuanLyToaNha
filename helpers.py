"""Hàm dùng chung cho các module CRUD.

- lay_nhieu / lay_mot : đọc dữ liệu (SELECT)
- thuc_thi            : INSERT / UPDATE / DELETE, tự commit, tự rollback khi lỗi
- dich_loi            : đổi lỗi MySQL thành câu tiếng Việt cho người dùng
"""
import re
from mysql.connector import Error
from db import get_connection

# Tên ràng buộc CHECK trong file .sql  ->  thông báo hiển thị
CHECK_MSG = {
    'chk_ct_masothue': 'Mã số thuế phải gồm 10 hoặc 13 chữ số.',
    'chk_ct_von':      'Vốn điều lệ không được âm.',
    'chk_ct_sonv':     'Số nhân viên không được âm.',
    'chk_ct_dientich': 'Diện tích thuê phải lớn hơn 0.',
    'chk_ct_dongia':   'Đơn giá thuê phải lớn hơn 0.',
    'chk_sd_ngay':     'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.',
}


def dich_loi(e):
    """Đổi lỗi mysql.connector thành thông báo thân thiện."""
    errno = getattr(e, 'errno', None)
    msg = getattr(e, 'msg', None) or str(e)

    if errno == 1644:                      # SIGNAL SQLSTATE '45000' từ TRIGGER
        return msg                         # chính là câu trong MESSAGE_TEXT
    if errno == 1062:                      # trùng khóa
        if 'MaSoThue' in msg:
            return 'Mã số thuế này đã tồn tại.'
        if 'CCCD' in msg:
            return 'Số CCCD này đã tồn tại.'
        if 'PRIMARY' in msg:
            return 'Mã này đã tồn tại, hãy chọn mã khác.'
        return 'Dữ liệu bị trùng với một bản ghi đã có.'
    if errno == 1451:                      # xóa bản ghi cha còn bản ghi con
        return 'Không thể xóa vì còn dữ liệu liên quan (nhân viên, dịch vụ, thẻ...).'
    if errno == 1452:                      # khóa ngoại trỏ tới bản ghi không có
        return 'Mã tham chiếu không tồn tại (công ty, dịch vụ, nhân viên...).'
    if errno == 3819:                      # vi phạm CHECK
        m = re.search(r"'(\w+)'", msg)
        return CHECK_MSG.get(m.group(1) if m else '', 'Dữ liệu vi phạm ràng buộc của hệ thống.')
    if errno in (1048, 1364):
        return 'Có trường bắt buộc đang để trống.'
    if errno in (1265, 1292, 1366):
        return 'Có trường nhập sai định dạng (số / ngày).'
    return 'Lỗi cơ sở dữ liệu: ' + msg


def lay_nhieu(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def lay_mot(sql, params=()):
    ds = lay_nhieu(sql, params)
    return ds[0] if ds else None


def thuc_thi(sql, params=()):
    """Chạy INSERT/UPDATE/DELETE. Trả về (True, số_dòng) hoặc (False, thông_báo_lỗi)."""
    try:
        conn = get_connection()
    except Error as e:
        return False, 'Không kết nối được cơ sở dữ liệu: ' + str(e)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()                      # quên dòng này thì dữ liệu không được lưu
        return True, cur.rowcount
    except Error as e:
        conn.rollback()
        return False, dich_loi(e)
    finally:
        conn.close()
