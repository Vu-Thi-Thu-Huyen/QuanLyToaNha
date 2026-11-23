/* QUAN LY TOA NHA VAN PHONG */
/* Yeu cau: MySQL 8.0.16 tro len */
/*
   PHAN CONG THUC HIEN:
   - Chien (Nguoi 1): CONGTY, PHONG, quan ly cong ty, tien thue mat bang.
   - Diep Anh (Nguoi 2): NHANVIEN_CONGTY, THE_RA_VAO, LICHSU_RA_VAO,
     quan ly nhan vien cong ty va kiem soat ra vao.
   - Thuy (Nguoi 3): DICHVU, SUDUNGDICHVU, dang ky va tinh tien dich vu.
   - Quang Anh (Nguoi 4): BAC_LUONG, NHANVIEN_TOANHA, PHANCONG,
     quan ly nhan vien toa nha va tinh luong.
   - Cac phan truy van tong hop duoc ghi ro thanh vien phoi hop ben duoi.
*/
/* Neu muon tao lai tu dau, giu nguyen dong DROP DATABASE ben duoi.
   Luu y: lenh nay se xoa toan bo du lieu trong database (ke ca TAIKHOAN). */
SET NAMES utf8mb4;
DROP DATABASE IF EXISTS QuanLyToaNha;
CREATE DATABASE IF NOT EXISTS QuanLyToaNha CHARACTER SET utf8mb4;
USE QuanLyToaNha;

/* ===================================================================== */
/* PHAN 1. CAC BANG */
/* Thu tu: CONGTY -> PHONG -> DICHVU -> VITRI_DICHVU -> NHANVIEN_CONGTY -> THE_RA_VAO */
/*         -> LICHSU_RA_VAO -> SUDUNGDICHVU -> BAC_LUONG -> NHANVIEN_TOANHA -> PHANCONG */
/*         -> TAIKHOAN */
/* ===================================================================== */

/* ---------- Nguoi 1 (Chien): CONGTY ---------- */
/* Dien tich va don gia thue KHONG luu o day nua: lay tu bang PHONG qua DiaChi. */
/* DiaChi phai la mot phong co trong bang PHONG, vd 'Tầng 5, phòng 505' (co trigger kiem tra). */
CREATE TABLE IF NOT EXISTS CONGTY (
    MaCT        VARCHAR(10)   PRIMARY KEY,
    TenCT       VARCHAR(150)  NOT NULL,
    MaSoThue    VARCHAR(14)   NOT NULL,                 -- 10 hoac 13 chu so
    VonDieuLe   DECIMAL(18,0) NOT NULL,
    LinhVuc     VARCHAR(100)  NOT NULL,
    SoNhanVien  INT           NOT NULL,                 -- so nhan vien cua cong ty (dung tinh bac nguoi)
    DiaChi      VARCHAR(150)  NOT NULL,
    MaPhong     VARCHAR(10)   NULL,                 -- phong dang thue (tang, phong)
    SoDienThoai VARCHAR(15)   NOT NULL,
    CONSTRAINT uq_ct_masothue   UNIQUE (MaSoThue),
    CONSTRAINT uq_ct_sodienthoai UNIQUE (SoDienThoai),
    CONSTRAINT uq_ct_diachi     UNIQUE (DiaChi),        -- moi phong chi co 1 cong ty thue
    CONSTRAINT chk_ct_masothue  CHECK (MaSoThue REGEXP '^[0-9]{10}([0-9]{3})?$'),
    CONSTRAINT chk_ct_von       CHECK (VonDieuLe >= 0),
    CONSTRAINT chk_ct_sonv      CHECK (SoNhanVien >= 0)
) ENGINE=InnoDB;

/* ---------- Nguoi 1 (Chien): PHONG ---------- */
/* Toa nha 10 tang, moi tang 6 phong (xx01 -> xx06). Cac phong cung so thu tu o cac tang */
/* co cung dien tich (501 va 601 deu 150 m2). Don gia thue la mot gia chung cho moi m2 (xem FN_DONGIA_M2). */
CREATE TABLE IF NOT EXISTS PHONG (
    MaPhong     VARCHAR(10)   PRIMARY KEY,
    Tang        INT           NOT NULL,
    DienTich    DECIMAL(8,2)  NOT NULL,                 -- m2
    CONSTRAINT chk_phong_tang     CHECK (Tang BETWEEN 1 AND 10),
    CONSTRAINT chk_phong_dientich CHECK (DienTich > 0)
) ENGINE=InnoDB;

/* ---------- Nguoi 3 (Thuy): DICHVU ---------- */
/* DonGia la GIA CO BAN MOT THANG cua dich vu (cho cong ty duoi 10 nguoi va duoi 100 m2). */
/* Gia thuc te = DonGia x he so (xem FN_HESO), tinh theo ti le ngay su dung / so ngay trong thang. */
CREATE TABLE IF NOT EXISTS DICHVU (
    MaDV      VARCHAR(10)   PRIMARY KEY,
    TenDV     VARCHAR(100)  NOT NULL,
    LoaiDV    VARCHAR(50)   NOT NULL,                   -- nhom dich vu: An ninh, Moi truong, Tien ich, Ky thuat
    DonGia    DECIMAL(15,2) NOT NULL,
    DonViTinh VARCHAR(30)   NOT NULL DEFAULT 'dong/thang',
    BatBuoc   BOOLEAN       NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_dv_dongia CHECK (DonGia > 0)
) ENGINE=InnoDB;

/* ---------- Nguoi 4 (Quang Anh): VITRI_DICHVU ---------- */
/* Danh sach vi tri lam viec theo tung dich vu (MaDV NULL = vi tri hanh chinh) */
CREATE TABLE IF NOT EXISTS VITRI_DICHVU (
    MaViTri  INT AUTO_INCREMENT PRIMARY KEY,
    MaDV     VARCHAR(10)  NULL,
    TenViTri VARCHAR(100) NOT NULL UNIQUE,
    HeSo     DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    CONSTRAINT fk_vtdv_dv FOREIGN KEY (MaDV) REFERENCES DICHVU(MaDV)
) ENGINE=InnoDB;

/* ---------- Nguoi 2 (Diep Anh): NHANVIEN_CONGTY, THE_RA_VAO, LICHSU_RA_VAO ---------- */
CREATE TABLE IF NOT EXISTS NHANVIEN_CONGTY (
    MaNV        VARCHAR(10)  PRIMARY KEY,
    MaCT        VARCHAR(10)  NOT NULL,
    HoTen       VARCHAR(100) NOT NULL,
    CCCD        VARCHAR(12)  NOT NULL UNIQUE,
    NgaySinh    DATE,
    GioiTinh    VARCHAR(10),
    SoDienThoai VARCHAR(15),
    ChucVu      VARCHAR(50),
    CONSTRAINT fk_nvct_ct FOREIGN KEY (MaCT) REFERENCES CONGTY(MaCT) ON DELETE CASCADE,
    CONSTRAINT chk_nvct_gioitinh CHECK (GioiTinh IS NULL OR GioiTinh IN ('Nam','Nu'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS THE_RA_VAO (
    MaThe      VARCHAR(10) PRIMARY KEY,
    MaNV       VARCHAR(10) NOT NULL,
    NgayCap    DATE        NOT NULL,
    NgayHetHan DATE,
    TrangThai  VARCHAR(20) NOT NULL DEFAULT 'HOAT_DONG',
    CONSTRAINT fk_the_nv FOREIGN KEY (MaNV) REFERENCES NHANVIEN_CONGTY(MaNV) ON DELETE CASCADE,
    CONSTRAINT chk_the_ngay CHECK (NgayHetHan IS NULL OR NgayHetHan >= NgayCap),
    CONSTRAINT chk_the_trangthai CHECK (TrangThai IN ('HOAT_DONG','BI_KHOA','HET_HAN'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS LICHSU_RA_VAO (
    MaLS     INT AUTO_INCREMENT PRIMARY KEY,
    MaThe    VARCHAR(10) NOT NULL,
    ThoiGian DATETIME    NOT NULL,
    ViTri    VARCHAR(20) NOT NULL,
    HanhDong VARCHAR(10) NOT NULL,
    CONSTRAINT fk_ls_the FOREIGN KEY (MaThe) REFERENCES THE_RA_VAO(MaThe) ON DELETE CASCADE,
    CONSTRAINT chk_ls_vitri   CHECK (ViTri IN ('TANG_1','B1','B2')),
    CONSTRAINT chk_ls_hanhdong CHECK (HanhDong IN ('VAO','RA'))
) ENGINE=InnoDB;

/* ---------- Nguoi 3 (Thuy): SUDUNGDICHVU ---------- */
CREATE TABLE IF NOT EXISTS SUDUNGDICHVU (
    MaSD        INT AUTO_INCREMENT PRIMARY KEY,
    MaCT        VARCHAR(10) NOT NULL,
    MaDV        VARCHAR(10) NOT NULL,
    NgayBatDau  DATE NOT NULL,
    NgayKetThuc DATE NULL,
    CONSTRAINT fk_sd_ct FOREIGN KEY (MaCT) REFERENCES CONGTY(MaCT) ON DELETE CASCADE,
CONSTRAINT fk_sd_dv FOREIGN KEY (MaDV) REFERENCES DICHVU(MaDV),
    CONSTRAINT chk_sd_ngay CHECK (NgayKetThuc IS NULL OR NgayKetThuc >= NgayBatDau),
    /* Cho phep dang ky lai cung dich vu o dot khac; trigger chan khoang ngay chong lap */
    CONSTRAINT uq_sd_dot UNIQUE (MaCT, MaDV, NgayBatDau)
) ENGINE=InnoDB;

/* ---------- Nguoi 4 (Quang Anh): BAC_LUONG, NHANVIEN_TOANHA, PHANCONG ---------- */
/* Bac cong viec (thay doi theo thang) quyet dinh luong co ban va ti le hoa hong tren doanh thu dich vu */
CREATE TABLE IF NOT EXISTS BAC_LUONG (
    Bac        INT           PRIMARY KEY,
    LuongCoBan DECIMAL(15,2) NOT NULL,                  -- luong co ban 1 thang (26 ngay cong)
    TyLeHoaHong DECIMAL(5,4) NOT NULL,                  -- ti le tren doanh thu dich vu phu trach
    CONSTRAINT chk_bl_luong CHECK (LuongCoBan > 0),
    CONSTRAINT chk_bl_tyle  CHECK (TyLeHoaHong >= 0 AND TyLeHoaHong <= 1)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS NHANVIEN_TOANHA (
    MaNV        VARCHAR(10)  PRIMARY KEY,
    HoTen       VARCHAR(100) NOT NULL,
    CCCD        VARCHAR(12)  NOT NULL UNIQUE,
    NgaySinh    DATE,
    GioiTinh    VARCHAR(10),
    DiaChi      VARCHAR(200),
    SoDienThoai VARCHAR(15),
    CONSTRAINT chk_nvtn_gioitinh CHECK (GioiTinh IS NULL OR GioiTinh IN ('Nam','Nu'))
) ENGINE=InnoDB;

/* Moi dong = vi tri, bac, dich vu cua 1 nhan vien trong 1 thang (doi vi tri theo thang) */
CREATE TABLE IF NOT EXISTS PHANCONG (
    MaPC       INT AUTO_INCREMENT PRIMARY KEY,
    MaNV       VARCHAR(10)  NOT NULL,
    MaDV       VARCHAR(10)  NULL,                       -- NULL = khong thuoc dich vu cu the (hanh chinh, ke toan)
    ViTri      VARCHAR(100) NOT NULL,                   -- vi tri / khu vuc lam viec
    Bac        INT          NOT NULL,                   -- bac cong viec trong thang
    Thang      INT          NOT NULL,
    Nam        INT          NOT NULL,
    HeSoViTri  DECIMAL(4,2) NOT NULL DEFAULT 1.00,      -- he so theo vi tri (giam sat, truc dem... cao hon)
    SoNgayCong INT          NOT NULL DEFAULT 26,
    CONSTRAINT fk_pc_nv  FOREIGN KEY (MaNV) REFERENCES NHANVIEN_TOANHA(MaNV),
    CONSTRAINT fk_pc_dv  FOREIGN KEY (MaDV) REFERENCES DICHVU(MaDV),
    CONSTRAINT fk_pc_bac FOREIGN KEY (Bac)  REFERENCES BAC_LUONG(Bac),
    CONSTRAINT chk_pc_thang  CHECK (Thang BETWEEN 1 AND 12),
    CONSTRAINT chk_pc_nam    CHECK (Nam >= 2000),
    CONSTRAINT chk_pc_heso   CHECK (HeSoViTri > 0),
    CONSTRAINT chk_pc_songay CHECK (SoNgayCong BETWEEN 0 AND 31),
    CONSTRAINT uq_pc_nv_thang UNIQUE (MaNV, Thang, Nam)
) ENGINE=InnoDB;

/* ---------- Tai khoan dang nhap cua ung dung ---------- */
CREATE TABLE IF NOT EXISTS TAIKHOAN (
    ma_tai_khoan  INT AUTO_INCREMENT PRIMARY KEY,
    ten_dang_nhap VARCHAR(50)  NOT NULL UNIQUE,
    mat_khau_hash VARCHAR(255) NOT NULL,
    vai_tro       ENUM('admin','nhanvien') NOT NULL DEFAULT 'nhanvien',
    trang_thai    TINYINT(1)   NOT NULL DEFAULT 1,
    ma_nv_toanha  VARCHAR(10)  NULL,
    CONSTRAINT fk_tk_nvtn FOREIGN KEY (ma_nv_toanha) REFERENCES NHANVIEN_TOANHA(MaNV)
) ENGINE=InnoDB;

/* ===================================================================== */
/* PHAN 2. VIEW PHONG (dung chung cho ham, thu tuc, view ben duoi) */
/* ===================================================================== */

/* Phong kem dia chi dang chuoi, de noi voi CONGTY.DiaChi */
CREATE OR REPLACE VIEW V_PHONG AS
SELECT MaPhong, Tang, DienTich,
       CONCAT('Tầng ', Tang, ', phòng ', MaPhong) AS DiaChi
FROM PHONG;

/* ===================================================================== */
/* PHAN 3. HAM TINH TOAN VA TRIGGER */
/* ===================================================================== */
DELIMITER $$

/* Don gia thue chung cho moi m2, don vi dong/m2/thang. Muon doi gia chi sua so nay. */
DROP FUNCTION IF EXISTS FN_DONGIA_M2$$
CREATE FUNCTION FN_DONGIA_M2()
RETURNS DECIMAL(15,2) DETERMINISTIC
BEGIN
    RETURN 200000;
END$$

/* He so don gia dich vu = 1 + 5% x (bac nguoi + bac dien tich) */
/*   bac nguoi     = 0 neu < 10 nguoi, nguoc lai 1 + (n - 10) DIV 5 */
/*   bac dien tich = 0 neu < 100 m2,   nguoc lai 1 + (dt - 100) DIV 10 */
DROP FUNCTION IF EXISTS FN_HESO$$
CREATE FUNCTION FN_HESO(p_sonv INT, p_dt DECIMAL(10,2))
RETURNS DECIMAL(6,2) DETERMINISTIC
BEGIN
    DECLARE v_bac_nguoi INT DEFAULT 0;
    DECLARE v_bac_dt INT DEFAULT 0;
    IF p_sonv >= 10 THEN
        SET v_bac_nguoi = 1 + FLOOR((p_sonv - 10) / 5);
    END IF;
    IF p_dt >= 100 THEN
        SET v_bac_dt = 1 + FLOOR((p_dt - 100) / 10);
    END IF;
    RETURN 1 + 0.05 * (v_bac_nguoi + v_bac_dt);
END$$

/* So ngay su dung trong khoang [p_dau, p_den], tinh ca hai dau, khong am */
DROP FUNCTION IF EXISTS FN_NGAY_SD$$
CREATE FUNCTION FN_NGAY_SD(p_batdau DATE, p_ketthuc DATE, p_dau DATE, p_den DATE)
RETURNS INT DETERMINISTIC
BEGIN
    RETURN GREATEST(
        DATEDIFF(LEAST(IFNULL(p_ketthuc, p_den), p_den), GREATEST(p_batdau, p_dau)) + 1, 0);
END$$

/* Tong tien dich vu cua 1 cong ty trong thang */
/*   tien = DonGia x he so x (so ngay da dung / so ngay cua thang) */
/*   so ngay dung tinh tu max(ngay dang ky, dau thang) den min(ngay ket thuc, cuoi thang, hom nay) */
/*   dien tich de tinh he so lay tu phong (V_PHONG) ma cong ty dang thue */
DROP FUNCTION IF EXISTS FN_TONG_TIEN_DV_CONGTY$$
CREATE FUNCTION FN_TONG_TIEN_DV_CONGTY(p_mact VARCHAR(10), p_thang INT, p_nam INT)
RETURNS DECIMAL(18,0) READS SQL DATA
BEGIN
    DECLARE v_dau  DATE;
    DECLARE v_cuoi DATE;
    DECLARE v_den  DATE;
    DECLARE v_tong DECIMAL(18,4);
    SET v_dau  = STR_TO_DATE(CONCAT(p_nam, '-', LPAD(p_thang, 2, '0'), '-01'), '%Y-%m-%d');
    SET v_cuoi = LAST_DAY(v_dau);
    SET v_den  = LEAST(v_cuoi, CURDATE());

    SELECT COALESCE(SUM(
               d.DonGia * FN_HESO(c.SoNhanVien, ph.DienTich)
               * FN_NGAY_SD(s.NgayBatDau, s.NgayKetThuc, v_dau, v_den) / DAY(v_cuoi)), 0)
      INTO v_tong
      FROM SUDUNGDICHVU s
      JOIN CONGTY c   ON c.MaCT = s.MaCT
      JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
      JOIN DICHVU d   ON d.MaDV = s.MaDV
     WHERE s.MaCT = p_mact;
    RETURN ROUND(v_tong, 0);
END$$

/* Doanh thu cua 1 dich vu trong thang (tong tien tat ca cong ty phai tra cho dich vu do) */
DROP FUNCTION IF EXISTS FN_DOANHTHU_DICHVU$$
CREATE FUNCTION FN_DOANHTHU_DICHVU(p_madv VARCHAR(10), p_thang INT, p_nam INT)
RETURNS DECIMAL(18,0) READS SQL DATA
BEGIN
    DECLARE v_dau  DATE;
    DECLARE v_cuoi DATE;
    DECLARE v_den  DATE;
    DECLARE v_tong DECIMAL(18,4);
    SET v_dau  = STR_TO_DATE(CONCAT(p_nam, '-', LPAD(p_thang, 2, '0'), '-01'), '%Y-%m-%d');
    SET v_cuoi = LAST_DAY(v_dau);
    SET v_den  = LEAST(v_cuoi, CURDATE());

    SELECT COALESCE(SUM(
               d.DonGia * FN_HESO(c.SoNhanVien, ph.DienTich)
               * FN_NGAY_SD(s.NgayBatDau, s.NgayKetThuc, v_dau, v_den) / DAY(v_cuoi)), 0)
      INTO v_tong
      FROM SUDUNGDICHVU s
      JOIN CONGTY c   ON c.MaCT = s.MaCT
      JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
      JOIN DICHVU d   ON d.MaDV = s.MaDV
     WHERE s.MaDV = p_madv;
    RETURN ROUND(v_tong, 0);
END$$

/* ---------- Rang buoc ve so luong ban ghi (the hien trong ung dung qua thong bao loi) ---------- */

/* (a) So nhan vien thuc te cua cong ty khong vuot qua CONGTY.SoNhanVien */
DROP TRIGGER IF EXISTS TRG_NVCT_BI$$
CREATE TRIGGER TRG_NVCT_BI BEFORE INSERT ON NHANVIEN_CONGTY
FOR EACH ROW
BEGIN
    IF (SELECT COUNT(*) FROM NHANVIEN_CONGTY WHERE MaCT = NEW.MaCT)
       >= (SELECT SoNhanVien FROM CONGTY WHERE MaCT = NEW.MaCT) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cong ty da du so nhan vien cho phep (CONGTY.SoNhanVien)';
    END IF;
END$$

DROP TRIGGER IF EXISTS TRG_NVCT_BU$$
CREATE TRIGGER TRG_NVCT_BU BEFORE UPDATE ON NHANVIEN_CONGTY
FOR EACH ROW
BEGIN
    IF NEW.MaCT <> OLD.MaCT
       AND (SELECT COUNT(*) FROM NHANVIEN_CONGTY WHERE MaCT = NEW.MaCT)
           >= (SELECT SoNhanVien FROM CONGTY WHERE MaCT = NEW.MaCT) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cong ty moi da du so nhan vien cho phep';
    END IF;
END$$

/* (a2) Dia chi cong ty phai la mot phong co that trong bang PHONG */
DROP TRIGGER IF EXISTS TRG_CT_BI$$
CREATE TRIGGER TRG_CT_BI BEFORE INSERT ON CONGTY
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM PHONG
                   WHERE CONCAT('Tầng ', Tang, ', phòng ', MaPhong) = NEW.DiaChi) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Dia chi phai la mot phong co trong bang PHONG (vd: Tang 5, phong 501)';
    END IF;
END$$

DROP TRIGGER IF EXISTS TRG_CT_BU$$
CREATE TRIGGER TRG_CT_BU BEFORE UPDATE ON CONGTY
FOR EACH ROW
BEGIN
    IF NEW.SoNhanVien < (SELECT COUNT(*) FROM NHANVIEN_CONGTY WHERE MaCT = NEW.MaCT) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'SoNhanVien khong duoc nho hon so nhan vien dang co cua cong ty';
    END IF;
    IF NEW.DiaChi <> OLD.DiaChi
       AND NOT EXISTS (SELECT 1 FROM PHONG
                       WHERE CONCAT('Tầng ', Tang, ', phòng ', MaPhong) = NEW.DiaChi) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Dia chi phai la mot phong co trong bang PHONG (vd: Tang 5, phong 501)';
    END IF;
END$$

/* (b) Moi nhan vien chi co mot the dang hoat dong */
DROP TRIGGER IF EXISTS TRG_THE_BI$$
CREATE TRIGGER TRG_THE_BI BEFORE INSERT ON THE_RA_VAO
FOR EACH ROW
BEGIN
    IF NEW.TrangThai = 'HOAT_DONG'
       AND EXISTS (SELECT 1 FROM THE_RA_VAO t
                   WHERE t.MaNV = NEW.MaNV AND t.TrangThai = 'HOAT_DONG'
                     AND (t.NgayHetHan IS NULL OR t.NgayHetHan >= CURDATE())) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nhan vien da co the dang hoat dong';
    END IF;
END$$

/* (c) Dich vu bat buoc (Ve sinh, Bao ve): khong duoc xoa / ket thuc */
DROP TRIGGER IF EXISTS TRG_SD_BI$$
CREATE TRIGGER TRG_SD_BI BEFORE INSERT ON SUDUNGDICHVU
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM SUDUNGDICHVU s
               WHERE s.MaCT = NEW.MaCT AND s.MaDV = NEW.MaDV
                 AND s.NgayBatDau <= IFNULL(NEW.NgayKetThuc, '9999-12-31')
                 AND IFNULL(s.NgayKetThuc, '9999-12-31') >= NEW.NgayBatDau) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cong ty da dang ky dich vu nay trong khoang ngay bi chong lap';
    END IF;
END$$

DROP TRIGGER IF EXISTS TRG_SD_BU$$
CREATE TRIGGER TRG_SD_BU BEFORE UPDATE ON SUDUNGDICHVU
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM SUDUNGDICHVU s
               WHERE s.MaSD <> NEW.MaSD
                 AND s.MaCT = NEW.MaCT AND s.MaDV = NEW.MaDV
                 AND s.NgayBatDau <= IFNULL(NEW.NgayKetThuc, '9999-12-31')
                 AND IFNULL(s.NgayKetThuc, '9999-12-31') >= NEW.NgayBatDau) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khoang ngay bi chong lap voi dang ky khac';
    END IF;
    IF OLD.NgayKetThuc IS NULL AND NEW.NgayKetThuc IS NOT NULL
       AND (SELECT BatBuoc FROM DICHVU WHERE MaDV = NEW.MaDV) = TRUE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Dich vu bat buoc (Ve sinh, Bao ve) khong duoc ket thuc';
    END IF;
END$$

DROP TRIGGER IF EXISTS TRG_SD_BD$$
CREATE TRIGGER TRG_SD_BD BEFORE DELETE ON SUDUNGDICHVU
FOR EACH ROW
BEGIN
    IF (SELECT BatBuoc FROM DICHVU WHERE MaDV = OLD.MaDV) = TRUE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong duoc xoa dang ky dich vu bat buoc';
    END IF;
END$$

DROP TRIGGER IF EXISTS TRG_DV_BD$$
CREATE TRIGGER TRG_DV_BD BEFORE DELETE ON DICHVU
FOR EACH ROW
BEGIN
    IF OLD.BatBuoc = TRUE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Khong duoc xoa dich vu bat buoc';
    END IF;
END$$

/* ===================================================================== */
/* PHAN 4. THU TUC CHO TRUY VAN */
/* ===================================================================== */

/* Truy van 2: nhan vien cong ty, so lan va vi tri ra/vao trong ngay chon */
DROP PROCEDURE IF EXISTS PR_RAVAO_NGAY$$
CREATE PROCEDURE PR_RAVAO_NGAY(IN p_ngay DATE)
BEGIN
    SELECT
        (SELECT t.MaThe
         FROM THE_RA_VAO t
         WHERE t.MaNV = nv.MaNV
         ORDER BY (t.TrangThai = 'HOAT_DONG') DESC,
                  t.NgayCap DESC, t.MaThe DESC
         LIMIT 1) AS MaThe,
        nv.MaNV,
        nv.HoTen,
        nv.CCCD,
        nv.NgaySinh,
        nv.SoDienThoai,
        c.TenCT,
        COALESCE(tk.ViTri, 'CHUA_RA_VAO') AS ViTri,
        COALESCE(tk.SoLanVao, 0) AS SoLanVao,
        COALESCE(tk.SoLanRa, 0) AS SoLanRa,
        COALESCE(tk.SoLanVao, 0) + COALESCE(tk.SoLanRa, 0) AS TongSoLan
    FROM NHANVIEN_CONGTY nv
    JOIN CONGTY c ON c.MaCT = nv.MaCT
    LEFT JOIN (
        SELECT t.MaNV, ls.ViTri,
               SUM(ls.HanhDong = 'VAO') AS SoLanVao,
               SUM(ls.HanhDong = 'RA')  AS SoLanRa
        FROM THE_RA_VAO t
        JOIN LICHSU_RA_VAO ls ON ls.MaThe = t.MaThe
        WHERE ls.ThoiGian >= p_ngay AND ls.ThoiGian < p_ngay + INTERVAL 1 DAY
        GROUP BY t.MaNV, ls.ViTri
    ) tk ON tk.MaNV = nv.MaNV
    ORDER BY nv.MaNV, tk.ViTri;
END$$

DELIMITER ;

/* Chi tiet tien dich vu cua tung cong ty trong thang (viet thanh 1 cau lenh, khong can DELIMITER) */
DROP PROCEDURE IF EXISTS PR_TIEN_DICHVU_CHITIET;
CREATE PROCEDURE PR_TIEN_DICHVU_CHITIET(IN p_thang INT, IN p_nam INT)
SELECT c.MaCT, c.TenCT, d.MaDV, d.TenDV, d.DonGia,
       FN_HESO(c.SoNhanVien, ph.DienTich) AS HeSo,
       FN_NGAY_SD(s.NgayBatDau, s.NgayKetThuc, k.dau, k.den) AS SoNgay,
       DAY(k.cuoi) AS SoNgayTrongThang,
       ROUND(d.DonGia * FN_HESO(c.SoNhanVien, ph.DienTich)
             * FN_NGAY_SD(s.NgayBatDau, s.NgayKetThuc, k.dau, k.den) / DAY(k.cuoi), 0) AS TienDV
FROM (SELECT STR_TO_DATE(CONCAT(p_nam, '-', LPAD(p_thang, 2, '0'), '-01'), '%Y-%m-%d') AS dau,
             LAST_DAY(STR_TO_DATE(CONCAT(p_nam, '-', LPAD(p_thang, 2, '0'), '-01'), '%Y-%m-%d')) AS cuoi,
             LEAST(LAST_DAY(STR_TO_DATE(CONCAT(p_nam, '-', LPAD(p_thang, 2, '0'), '-01'), '%Y-%m-%d')),
                   CURDATE()) AS den) k
CROSS JOIN SUDUNGDICHVU s
JOIN CONGTY c   ON c.MaCT = s.MaCT
JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
JOIN DICHVU d   ON d.MaDV = s.MaDV
ORDER BY c.MaCT, d.MaDV, s.NgayBatDau;

/* ===================================================================== */
/* PHAN 5. VIEW (TRUY VAN VA KIEM TRA RANG BUOC) */
/* ===================================================================== */

/* Truy van 1: thong tin cong ty + tien thue + tien dich vu (thang hien tai, tinh den hom nay) */
/*   Tien thue = dien tich x don gia m2 (dong/m2/thang)*/
/*   LEFT JOIN: cong ty chua khop phong nao van hien, dien tich va tien thue = 0 */
/* Dung:  SELECT * FROM V_TONG_CHIPHI_CONGTY ORDER BY TongChiPhi DESC; */
CREATE OR REPLACE VIEW V_TONG_CHIPHI_CONGTY AS
SELECT t.*, t.TienThue + t.TienDichVu AS TongChiPhi
FROM (
    SELECT c.MaCT, c.TenCT, c.MaSoThue, c.VonDieuLe, c.LinhVuc, c.SoNhanVien,
           c.DiaChi, c.SoDienThoai,
           COALESCE(ph.DienTich, 0) AS DienTichThue,
           FN_DONGIA_M2()           AS DonGiaThue,
           ROUND(COALESCE(ph.DienTich, 0) * FN_DONGIA_M2(), 0) AS TienThue,
           FN_TONG_TIEN_DV_CONGTY(c.MaCT, MONTH(CURDATE()), YEAR(CURDATE())) AS TienDichVu
    FROM CONGTY c
    LEFT JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
) t;

/* Danh sach phong va trang thai (Da thue / Trong) kem cong ty dang thue */
/* Dung:  SELECT * FROM V_PHONG_THUE ORDER BY Tang, MaPhong; */
CREATE OR REPLACE VIEW V_PHONG_THUE AS
SELECT p.MaPhong, p.DienTich,
       FN_DONGIA_M2()                        AS DonGiaThue,
       ROUND(p.DienTich * FN_DONGIA_M2(), 0) AS TienThue,
       p.Tang,
       c.MaCT, c.TenCT,
       CASE WHEN c.MaCT IS NULL THEN 'Trống' ELSE 'Đã thuê' END AS TrangThai
FROM V_PHONG p
LEFT JOIN CONGTY c ON c.DiaChi = p.DiaChi;

/* Truy van 3: bang luong nhan vien toa nha theo thang */
/*   Luong = LuongCoBan(bac) / 26 x SoNgayCong x HeSoViTri */
/*         + TyLeHoaHong(bac) x DoanhThu dich vu phu trach / so nguoi cung phu trach dich vu do trong thang */
/* Dung:  SELECT * FROM V_BANG_LUONG WHERE Thang = 11 AND Nam = 2026 ORDER BY TongLuong DESC; */
CREATE OR REPLACE VIEW V_BANG_LUONG AS
SELECT nv.MaNV, nv.HoTen, nv.DiaChi, nv.SoDienThoai,
       p.Thang, p.Nam, p.Bac, p.ViTri,
       COALESCE(dv.TenDV, 'Không thuộc dịch vụ cụ thể') AS TenDV,
       p.SoNgayCong, p.HeSoViTri, bl.LuongCoBan,
       ROUND(bl.LuongCoBan / 26 * p.SoNgayCong * p.HeSoViTri, 0) AS LuongTheoViTri,
       p.DoanhThuDV, p.SoNguoiCungDV,
       ROUND(bl.TyLeHoaHong * p.DoanhThuDV / p.SoNguoiCungDV, 0) AS HoaHong,
       ROUND(bl.LuongCoBan / 26 * p.SoNgayCong * p.HeSoViTri, 0)
         + ROUND(bl.TyLeHoaHong * p.DoanhThuDV / p.SoNguoiCungDV, 0) AS TongLuong
FROM (
    SELECT pc.*,
           CASE WHEN pc.MaDV IS NULL THEN 0
                ELSE FN_DOANHTHU_DICHVU(pc.MaDV, pc.Thang, pc.Nam) END AS DoanhThuDV,
           COUNT(*) OVER (PARTITION BY pc.MaDV, pc.Thang, pc.Nam) AS SoNguoiCungDV
    FROM PHANCONG pc
) p
JOIN NHANVIEN_TOANHA nv ON nv.MaNV = p.MaNV
JOIN BAC_LUONG bl ON bl.Bac = p.Bac
LEFT JOIN DICHVU dv ON dv.MaDV = p.MaDV;

/* Kiem tra rang buoc: cong ty hien dang THIEU dich vu bat buoc (rong = hop le) */
CREATE OR REPLACE VIEW V_CONGTY_THIEU_DV_BATBUOC AS
SELECT c.MaCT, c.TenCT, d.MaDV, d.TenDV
FROM CONGTY c
JOIN DICHVU d ON d.BatBuoc = TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM SUDUNGDICHVU s
    WHERE s.MaCT = c.MaCT AND s.MaDV = d.MaDV
      AND s.NgayBatDau <= CURDATE()
      AND (s.NgayKetThuc IS NULL OR s.NgayKetThuc >= CURDATE())
);

/* Kiem tra rang buoc: so nhan vien thuc te / so nhan vien cho phep cua tung cong ty */
CREATE OR REPLACE VIEW V_SO_NHANVIEN_CONGTY AS
SELECT c.MaCT, c.TenCT, c.SoNhanVien AS ChoPhep,
       COUNT(nv.MaNV) AS HienCo,
       c.SoNhanVien - COUNT(nv.MaNV) AS ConTrong
FROM CONGTY c
LEFT JOIN NHANVIEN_CONGTY nv ON nv.MaCT = c.MaCT
GROUP BY c.MaCT, c.TenCT, c.SoNhanVien;

/* Kiem tra rang buoc: nhan vien cong ty chua co the dang hoat dong (rong = hop le) */
CREATE OR REPLACE VIEW V_NV_CHUA_CO_THE AS
SELECT nv.MaNV, nv.HoTen, nv.MaCT
FROM NHANVIEN_CONGTY nv
WHERE NOT EXISTS (
    SELECT 1 FROM THE_RA_VAO t
    WHERE t.MaNV = nv.MaNV AND t.TrangThai = 'HOAT_DONG'
      AND (t.NgayHetHan IS NULL OR t.NgayHetHan >= CURDATE())
);

/* ===================================================================== */
/* PHAN 6. DU LIEU MAU */
/* ===================================================================== */

/* ---------- PHONG: 10 tang x 6 phong = 60 phong ---------- */
/* Dien tich theo so thu tu phong, cac tang giong nhau:
     xx01: 150 m2   xx02: 300 m2   xx03: 100 m2
     xx04: 250 m2   xx05: 120 m2   xx06: 200 m2 */
INSERT IGNORE INTO PHONG (MaPhong, Tang, DienTich)
SELECT CONCAT(t.n, LPAD(p.n, 2, '0')), t.n,
       CASE p.n WHEN 1 THEN 150 WHEN 2 THEN 300 WHEN 3 THEN 100
                WHEN 4 THEN 250 WHEN 5 THEN 120 ELSE 200 END
FROM (SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
      UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
      UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10) t
CROSS JOIN
     (SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
      UNION ALL SELECT 5 UNION ALL SELECT 6) p;


/* ---------- CONGTY (10 cong ty, moi cong ty thue 1 phong trong bang PHONG) ---------- */
INSERT IGNORE INTO CONGTY

(MaCT, TenCT, MaSoThue, VonDieuLe, LinhVuc, SoNhanVien, DiaChi, SoDienThoai) VALUES
('CT001', 'Công ty TNHH Phần mềm Sao Việt',    '0101234561',  5000000000, 'Phần mềm',             12, 'Tầng 5, phòng 505',   '0241234501'),
('CT002', 'Công ty CP Thương mại Hòa Bình',    '0101234562',  2000000000, 'Thương mại',            8, 'Tầng 3, phòng 303',   '0241234502'),
('CT003', 'Công ty CP Tài chính Đại Phát',     '0101234563', 20000000000, 'Tài chính',            25, 'Tầng 8, phòng 804',   '0241234503'),
('CT004', 'Công ty TNHH Thiết kế Nhà Xanh',    '0101234564',  1500000000, 'Thiết kế - xây dựng',  10, 'Tầng 4, phòng 403',   '0241234504'),
('CT005', 'Công ty CP Truyền thông Việt Media','0101234565',  3000000000, 'Truyền thông',         15, 'Tầng 6, phòng 605',   '0241234505'),
('CT006', 'Công ty TNHH Tư vấn Luật An Phát',  '0101234566',  1000000000, 'Tư vấn pháp lý',        6, 'Tầng 2, phòng 203',   '0241234506'),
('CT007', 'Công ty CP Công nghệ Minh Quang',   '0101234567', 50000000000, 'Công nghệ thông tin',  40, 'Tầng 10, phòng 1002', '0241234507'),
('CT008', 'Công ty TNHH Du lịch Biển Xanh',    '0101234568',   800000000, 'Du lịch',                9, 'Tầng 2, phòng 201',   '0241234508'),
('CT009', 'Công ty CP Giáo dục Tri Thức',      '0101234569',  4000000000, 'Giáo dục',             18, 'Tầng 7, phòng 701',   '0241234509'),
('CT010', 'Công ty TNHH Logistics Nhanh',      '0101234570',  6000000000, 'Vận tải - logistics',  30, 'Tầng 9, phòng 902',   '0241234510');

/* ---------- DICHVU (don gia = gia co ban 1 thang) ---------- */
INSERT IGNORE INTO DICHVU (MaDV, TenDV, LoaiDV, DonGia, DonViTinh, BatBuoc) VALUES
('DV01', 'Vệ sinh',          'Môi trường', 5000000,  'đồng/tháng', TRUE),
('DV02', 'Ăn uống',          'Tiện ích',   8000000,  'đồng/tháng', FALSE),
('DV03', 'Trông giữ xe',     'Tiện ích',   3000000,  'đồng/tháng', FALSE),
('DV04', 'Bảo vệ',           'An ninh',    10000000, 'đồng/tháng', TRUE),
('DV05', 'Bảo trì thiết bị', 'Kỹ thuật',   4000000,  'đồng/tháng', FALSE);

/* ---------- VITRI_DICHVU ---------- */
INSERT IGNORE INTO VITRI_DICHVU (MaDV, TenViTri, HeSo) VALUES
-- DV01: Vệ sinh
('DV01', 'Vệ sinh sảnh và tầng 1-5',        1.00),
('DV01', 'Vệ sinh tầng 6-10',               1.00),
('DV01', 'Vệ sinh tầng 11-15',              1.00),
('DV01', 'Vệ sinh khu vực hầm xe',          1.10),
('DV01', 'Vệ sinh kính mặt ngoài',          1.30),
-- DV02: Ăn uống
('DV02', 'Phục vụ căn tin tầng 1',          1.00),
('DV02', 'Thu ngân căn tin',                1.00),
('DV02', 'Bếp trưởng căn tin',              1.30),
-- DV03: Trông giữ xe
('DV03', 'Trông giữ xe hầm B1',             1.00),
('DV03', 'Trông giữ xe hầm B2',             1.00),
('DV03', 'Điều phối xe ra vào',             1.10),
-- DV04: Bảo vệ
('DV04', 'Bảo vệ cổng chính',               1.20),
('DV04', 'Bảo vệ cổng phụ',                 1.00),
('DV04', 'Bảo vệ bãi xe B1',                1.20),
('DV04', 'Tuần tra các tầng',               1.20),
('DV04', 'Trực camera phòng điều khiển',    1.30),
('DV04', 'Giám sát an ninh',                1.50),
-- DV05: Bảo trì thiết bị
('DV05', 'Bảo trì hệ thống điều hòa',       1.30),
('DV05', 'Bảo trì thang máy',               1.30),
('DV05', 'Bảo trì trạm điện tầng B2',       1.30),
('DV05', 'Kỹ thuật phòng máy tầng B2',      1.30),
('DV05', 'Bảo trì hệ thống PCCC',           1.40),
-- Hành chính (không thuộc dịch vụ)
(NULL,   'Kế toán ban quản lý',            1.10),
(NULL,   'Hành chính nhân sự',             1.10),
(NULL,   'Quản lý tòa nhà',                1.60);

/* ---------- SUDUNGDICHVU ---------- */
/* Moi cong ty dang ky dich vu bat buoc */
INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau, NgayKetThuc)
SELECT c.MaCT, d.MaDV, '2026-01-01', NULL
FROM CONGTY c JOIN DICHVU d ON d.BatBuoc = TRUE
WHERE c.MaCT <> 'CT011'
  AND NOT EXISTS (SELECT 1 FROM SUDUNGDICHVU s WHERE s.MaCT = c.MaCT AND s.MaDV = d.MaDV);

/* Cong ty tu 10 nhan vien tro len: them An uong, Trong giu xe */
INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau, NgayKetThuc)
SELECT c.MaCT, d.MaDV, '2026-02-01', NULL
FROM CONGTY c JOIN DICHVU d ON d.MaDV IN ('DV02', 'DV03')
WHERE c.SoNhanVien >= 10
  AND NOT EXISTS (SELECT 1 FROM SUDUNGDICHVU s WHERE s.MaCT = c.MaCT AND s.MaDV = d.MaDV);

/* Phong tu 100 m2 tro len: Bao tri thiet bi (dot cu da ket thuc + dot moi tu 01/09/2026) */
INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau, NgayKetThuc)
SELECT c.MaCT, 'DV05', '2026-01-01', '2026-06-30'
FROM CONGTY c
JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
WHERE ph.DienTich >= 100 AND c.MaCT <> 'CT011'
  AND NOT EXISTS (SELECT 1 FROM SUDUNGDICHVU s
                  WHERE s.MaCT = c.MaCT AND s.MaDV = 'DV05' AND s.NgayBatDau = '2026-01-01');

INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau, NgayKetThuc)
SELECT c.MaCT, 'DV05', '2026-09-01', NULL
FROM CONGTY c
JOIN V_PHONG ph ON ph.DiaChi = c.DiaChi
WHERE ph.DienTich >= 100 AND c.MaCT <> 'CT011'
  AND NOT EXISTS (SELECT 1 FROM SUDUNGDICHVU s
                  WHERE s.MaCT = c.MaCT AND s.MaDV = 'DV05' AND s.NgayBatDau = '2026-09-01');

/* ---------- NHANVIEN_CONGTY (CT001: 6 nguoi <= 12, CT002: 4 nguoi <= 8) ---------- */
INSERT IGNORE INTO NHANVIEN_CONGTY
(MaNV, MaCT, HoTen, CCCD, NgaySinh, GioiTinh, SoDienThoai, ChucVu) VALUES
('NV01', 'CT001', 'Nguyễn Văn An',   '001200000001', '2000-05-12', 'Nam', '0912345678', 'Nhân viên'),
('NV02', 'CT001', 'Trần Thị Bình',   '001199000002', '1999-08-20', 'Nu',  '0923456789', 'Kế toán'),
('NV03', 'CT002', 'Lê Văn Cường',    '001201000003', '2001-03-15', 'Nam', '0934567890', 'Nhân viên'),
('NV04', 'CT001', 'Phạm Thị Dung',   '001198000004', '1998-06-10', 'Nu',  '0945678901', 'Nhân sự'),
('NV05', 'CT001', 'Hoàng Văn Em',    '001200000005', '2000-09-22', 'Nam', '0956789012', 'Kỹ thuật'),
('NV06', 'CT001', 'Nguyễn Thị Hoa',  '001199000006', '1999-11-05', 'Nu',  '0967890123', 'Kế toán'),
('NV07', 'CT002', 'Đỗ Văn Hùng',     '001197000007', '1997-04-18', 'Nam', '0978901234', 'Trưởng phòng'),
('NV08', 'CT002', 'Bùi Thị Lan',     '001200000008', '2000-07-25', 'Nu',  '0989012345', 'Nhân viên'),
('NV09', 'CT002', 'Phan Văn Minh',   '001201000009', '2001-12-03', 'Nam', '0901234567', 'Kỹ thuật'),
('NV10', 'CT001', 'Lê Thị Ngọc',     '001202000010', '2002-02-14', 'Nu',  '0911122233', 'Nhân viên');

/* ---------- THE_RA_VAO ---------- */
/* Moi nhan vien mot the (THE01 cho NV01, ...); chi chen khi chua co the nao de chay lai khong loi trigger */
INSERT INTO THE_RA_VAO (MaThe, MaNV, NgayCap, NgayHetHan, TrangThai)
SELECT CONCAT('THE', SUBSTRING(nv.MaNV, 3)), nv.MaNV, '2026-01-01', '2027-01-01', 'HOAT_DONG'
FROM NHANVIEN_CONGTY nv
WHERE nv.MaNV <> 'NV11' AND NOT EXISTS (SELECT 1 FROM THE_RA_VAO t WHERE t.MaNV = nv.MaNV);

/* ---------- LICHSU_RA_VAO (chi chen khi bang con rong, tranh nhan doi khi chay lai) ---------- */
INSERT INTO LICHSU_RA_VAO (MaThe, ThoiGian, ViTri, HanhDong)
SELECT x.MaThe, x.ThoiGian, x.ViTri, x.HanhDong
FROM (
    SELECT 'THE01' AS MaThe, '2026-11-05 08:00:00' AS ThoiGian, 'TANG_1' AS ViTri, 'VAO' AS HanhDong
    UNION ALL SELECT 'THE01', '2026-11-05 17:30:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE10', '2026-11-05 08:20:00', 'B1', 'VAO'
    UNION ALL SELECT 'THE10', '2026-11-05 17:00:00', 'B1', 'RA'
    /* Ngay 06/11/2026 */
    UNION ALL SELECT 'THE01', '2026-11-06 08:00:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE01', '2026-11-06 12:00:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE01', '2026-11-06 13:00:00', 'B1', 'VAO'
    UNION ALL SELECT 'THE01', '2026-11-06 18:00:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE02', '2026-11-06 08:15:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE02', '2026-11-06 17:00:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE03', '2026-11-06 09:00:00', 'B2', 'VAO'
    UNION ALL SELECT 'THE03', '2026-11-06 18:00:00', 'B2', 'RA'
    UNION ALL SELECT 'THE04', '2026-11-06 07:50:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE04', '2026-11-06 16:40:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE05', '2026-11-06 08:10:00', 'B1', 'VAO'
    UNION ALL SELECT 'THE05', '2026-11-06 12:00:00', 'B1', 'RA'
    UNION ALL SELECT 'THE05', '2026-11-06 13:00:00', 'B1', 'VAO'
    UNION ALL SELECT 'THE05', '2026-11-06 18:00:00', 'B1', 'RA'
    UNION ALL SELECT 'THE06', '2026-11-06 08:05:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE06', '2026-11-06 17:15:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE07', '2026-11-06 07:55:00', 'B2', 'VAO'
    UNION ALL SELECT 'THE07', '2026-11-06 17:05:00', 'B2', 'RA'
    UNION ALL SELECT 'THE08', '2026-11-06 08:25:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE08', '2026-11-06 12:10:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE08', '2026-11-06 13:10:00', 'TANG_1', 'VAO'
    UNION ALL SELECT 'THE08', '2026-11-06 18:00:00', 'TANG_1', 'RA'
    UNION ALL SELECT 'THE09', '2026-11-06 09:10:00', 'B1', 'VAO'
    UNION ALL SELECT 'THE09', '2026-11-06 17:00:00', 'B1', 'RA'
) x
WHERE NOT EXISTS (SELECT 1 FROM LICHSU_RA_VAO);
/* Ghi chu: NV10 (THE10) chi co lich su ngay 05/11, khong co ngay 06/11 */
/* -> truy van ngay 06/11 van phai hien NV10 voi so lan = 0. */

/* ---------- BAC_LUONG ---------- */
INSERT IGNORE INTO BAC_LUONG (Bac, LuongCoBan, TyLeHoaHong) VALUES
(1, 5000000, 0.0050),
(2, 6000000, 0.0100),
(3, 8000000, 0.0150),
(4, 9000000, 0.0200);

/* ---------- NHANVIEN_TOANHA ---------- */
INSERT IGNORE INTO NHANVIEN_TOANHA
(MaNV, HoTen, CCCD, NgaySinh, GioiTinh, DiaChi, SoDienThoai) VALUES
('NVT01', 'Nguyễn Văn An',  '001090000101', '1990-05-15', 'Nam', '12 Nguyễn Trãi, Thanh Xuân, Hà Nội',  '0912345601'),
('NVT02', 'Trần Thị Bình',  '001095000102', '1995-08-20', 'Nu',  '45 Lê Văn Lương, Thanh Xuân, Hà Nội', '0912345602'),
('NVT03', 'Lê Hoàng Cường', '001092000103', '1992-11-10', 'Nam', '8 Khuất Duy Tiến, Thanh Xuân, Hà Nội','0912345603'),
('NVT04', 'Phạm Minh Dũng', '001088000104', '1988-03-02', 'Nam', '23 Nguyễn Xiển, Thanh Xuân, Hà Nội',  '0912345604'),
('NVT05', 'Võ Thị Hà',      '001093000105', '1993-07-19', 'Nu',  '77 Quan Nhân, Thanh Xuân, Hà Nội',    '0912345605'),
('NVT06', 'Đặng Quốc Huy',  '001091000106', '1991-01-25', 'Nam', '5 Hoàng Đạo Thúy, Cầu Giấy, Hà Nội',  '0912345606'),
('NVT07', 'Bùi Thu Lan',    '001094000107', '1994-09-09', 'Nu',  '31 Trần Duy Hưng, Cầu Giấy, Hà Nội',  '0912345607'),
('NVT08', 'Hoàng Văn Mạnh', '001089000108', '1989-12-30', 'Nam', '19 Láng Hạ, Đống Đa, Hà Nội',         '0912345608'),
('NVT09', 'Ngô Thị Nga',    '001096000109', '1996-04-12', 'Nu',  '64 Giải Phóng, Hai Bà Trưng, Hà Nội', '0912345609'),
('NVT10', 'Đỗ Văn Phúc',    '001097000110', '1997-06-06', 'Nam', '102 Nguyễn Tuân, Thanh Xuân, Hà Nội', '0912345610');

/* ---------- PHANCONG: thang 10 va 11/2026 (co nguoi doi bac, vi tri, dich vu giua hai thang) ---------- */
INSERT IGNORE INTO PHANCONG (MaNV, MaDV, ViTri, Bac, Thang, Nam, HeSoViTri, SoNgayCong) VALUES
('NVT01', 'DV04', 'Bảo vệ cổng chính',          2, 10, 2026, 1.20, 26),
('NVT02', 'DV01', 'Vệ sinh sảnh và tầng 1-5',   1, 10, 2026, 1.00, 24),
('NVT03', 'DV05', 'Kỹ thuật phòng máy tầng B2', 3, 10, 2026, 1.30, 26),
('NVT04', 'DV04', 'Giám sát an ninh',           4, 10, 2026, 1.50, 26),
('NVT05', 'DV01', 'Vệ sinh tầng 6-10',          1, 10, 2026, 1.00, 25),
('NVT06', 'DV04', 'Bảo vệ bãi xe B1',           2, 10, 2026, 1.20, 26),
('NVT07', 'DV03', 'Trông giữ xe hầm B2',        2, 10, 2026, 1.00, 26),
('NVT08', 'DV05', 'Bảo trì hệ thống điều hòa',  3, 10, 2026, 1.30, 22),
('NVT09', NULL,   'Kế toán ban quản lý',        3, 10, 2026, 1.10, 26),
('NVT10', 'DV04', 'Bảo vệ cổng phụ',            1, 10, 2026, 1.00, 20),

('NVT01', 'DV04', 'Bảo vệ cổng chính và B1',    2, 11, 2026, 1.20, 26),
('NVT02', 'DV01', 'Vệ sinh sảnh và tầng 1-5',   1, 11, 2026, 1.00, 24),
('NVT03', 'DV05', 'Bảo trì trạm điện tầng B2',  3, 11, 2026, 1.30, 26),
('NVT04', 'DV04', 'Giám sát an ninh',           4, 11, 2026, 1.50, 26),
('NVT05', 'DV01', 'Vệ sinh tầng 11-15',         1, 11, 2026, 1.00, 26),
('NVT06', 'DV04', 'Bảo vệ cổng phụ',            2, 11, 2026, 1.20, 26),
('NVT07', 'DV02', 'Phục vụ căn tin tầng 1',     2, 11, 2026, 1.00, 26),
('NVT08', 'DV05', 'Bảo trì thang máy',          3, 11, 2026, 1.30, 24),
('NVT09', NULL,   'Kế toán ban quản lý',        3, 11, 2026, 1.10, 26),
('NVT10', 'DV04', 'Bảo vệ cổng chính',          2, 11, 2026, 1.00, 26);

/* ===================================================================== */
/* DU LIEU DEMO CHO CAC VIEW KIEM TRA RANG BUOC */
/* ===================================================================== */

-- 1) Công ty mới chỉ đăng ký "Vệ sinh", chưa đăng ký "Bảo vệ" (bắt buộc)
INSERT IGNORE INTO CONGTY
(MaCT, TenCT, MaSoThue, VonDieuLe, LinhVuc, SoNhanVien, DiaChi, SoDienThoai) VALUES
('CT011', 'Công ty TNHH Nội thất Gia Phát', '0101234572', 1200000000, 'Nội thất', 8,
 'Tầng 3, phòng 305', '0241234512');

INSERT INTO SUDUNGDICHVU (MaCT, MaDV, NgayBatDau, NgayKetThuc)
SELECT 'CT011', 'DV01', '2026-11-01', NULL FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM SUDUNGDICHVU WHERE MaCT = 'CT011' AND MaDV = 'DV01');

-- 2) Nhân viên chưa được cấp thẻ ra vào
INSERT IGNORE INTO NHANVIEN_CONGTY
(MaNV, MaCT, HoTen, CCCD, NgaySinh, GioiTinh, SoDienThoai, ChucVu) VALUES
('NV11', 'CT001', 'Nguyễn Văn Phúc', '002200000032', '1997-06-15', 'Nam', '0911000032', 'Nhân viên');

UPDATE CONGTY c JOIN PHONG p
  ON c.DiaChi = CONCAT('Tầng ', p.Tang, ', phòng ', p.MaPhong)
SET c.MaPhong = p.MaPhong;

/* ===================================================================== */
/* PHAN 7. CAC CAU KIEM TRA (bo comment de thu) */
/* ===================================================================== */
/* Truy van 1: SELECT * FROM V_TONG_CHIPHI_CONGTY ORDER BY TongChiPhi DESC; */
/* Truy van 2: CALL PR_RAVAO_NGAY('2026-11-06'); */
/* Truy van 3: SELECT * FROM V_BANG_LUONG WHERE Thang = 11 AND Nam = 2026 ORDER BY TongLuong DESC; */
/* Chi tiet tien dich vu: CALL PR_TIEN_DICHVU_CHITIET(11, 2026); */
/* Danh sach phong va trang thai thue: SELECT * FROM V_PHONG_THUE ORDER BY Tang, MaPhong; */
/* Rang buoc (ket qua rong = hop le): */
/*   SELECT * FROM V_CONGTY_THIEU_DV_BATBUOC;   -- chi co CT011 thieu Bao ve (co y) */
/*   SELECT * FROM V_NV_CHUA_CO_THE;            -- chi co NV11 chua co the (co y) */
/*   SELECT * FROM V_SO_NHANVIEN_CONGTY; */
/* Thu rang buoc (phai bao loi): */
/*   DELETE FROM SUDUNGDICHVU WHERE MaDV = 'DV01' LIMIT 1; */
/*   INSERT INTO THE_RA_VAO (MaThe, MaNV, NgayCap) VALUES ('THE99', 'NV01', CURDATE()); */
/*   INSERT INTO CONGTY (MaCT, TenCT, MaSoThue, VonDieuLe, LinhVuc, SoNhanVien, DiaChi, SoDienThoai) */
/*   VALUES ('CT099', 'Test', '0101234599', 1, 'Test', 1, 'Tầng 99, phòng 999', '0241234599'); */
