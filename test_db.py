from db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ten_dang_nhap, vai_tro, trang_thai FROM TAIKHOAN")
    print("KET NOI OK:", cur.fetchall())
    conn.close()
except Exception as e:
    print("LOI THAT:", type(e).__name__, e)