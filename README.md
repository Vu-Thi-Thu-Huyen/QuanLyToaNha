# Quản lý tòa nhà văn phòng

Đồ án nhóm: hệ thống quản lý tòa nhà văn phòng (Flask + MySQL).

## Yêu cầu
- Python 3.10 trở lên
- MySQL 8.0 trở lên (kèm MySQL Workbench)

## Cài đặt
1. Cài thư viện:
```
python -m pip install -r requirements.txt
```
2. Tạo database: mở MySQL Workbench, mở file `database/QuanLyToaNha.sql` và chạy toàn bộ.
3. Tạo file cấu hình: copy `config.example.py` thành `config.py`, rồi điền mật khẩu MySQL của máy bạn.
```
copy config.example.py config.py
```
4. Chạy ứng dụng:
```
python app.py
```
5. Mở http://127.0.0.1:5000 và đăng nhập bằng tài khoản `admin` / `123456`.

## Cấu trúc thư mục
- `app.py`: khởi tạo ứng dụng, đăng nhập, dashboard
- `auth.py`: decorator `login_required`
- `db.py`: hàm `get_connection()` dùng chung
- `routes/`: mỗi module là một file Blueprint
- `templates/`: `base.html` dùng chung, mỗi trang kế thừa từ đó
- `static/`: CSS, JS, hình ảnh
- `database/`: file SQL tổng

## Quy ước nhóm
- Tên bảng IN HOA, tên cột PascalCase (MaCT, MaNV, MaDV...).
- Mã công ty `MaCT VARCHAR(10)`, mã dịch vụ `MaDV VARCHAR(10)`.
- Mỗi người làm một file trong `routes/`, template dùng `{% extends "base.html" %}`, bảng dùng class `data-table`.
- Dùng `get_connection()` trong `db.py`, không tự viết kết nối riêng.
- Không đưa `config.py` lên GitHub.

## Phân công
- Người 1: Công ty và chi phí thuê văn phòng
- Người 2: Nhân viên công ty và ra vào tòa nhà
- Người 3: Dịch vụ và tính tiền dịch vụ
- Người 4: Nhân viên tòa nhà và tính lương
- Người 5: Tích hợp hệ thống, giao diện, kiểm thử