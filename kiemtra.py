from db import get_connection

conn = get_connection()
cur = conn.cursor(dictionary=True)
cur.execute("SELECT MaCT, TenCT, VonDieuLe, TongChiPhi FROM V_TONG_CHIPHI_CONGTY ORDER BY TongChiPhi DESC")
for r in cur.fetchall()[:3]:
    print(r)
conn.close()