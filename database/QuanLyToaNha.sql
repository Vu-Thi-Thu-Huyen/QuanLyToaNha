CREATE DATABASE IF NOT EXISTS QuanLyToaNha CHARACTER SET utf8mb4;
USE QuanLyToaNha;

CREATE TABLE IF NOT EXISTS TAIKHOAN (
    ma_tai_khoan   INT AUTO_INCREMENT PRIMARY KEY,
    ten_dang_nhap  VARCHAR(50)  NOT NULL UNIQUE,
    mat_khau_hash  VARCHAR(255) NOT NULL,
    vai_tro        ENUM('admin','nhanvien') NOT NULL DEFAULT 'nhanvien',
    trang_thai     TINYINT(1)   NOT NULL DEFAULT 1,
    ma_nv_toanha   INT          NULL
);