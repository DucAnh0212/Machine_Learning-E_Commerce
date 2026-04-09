from app.core.database_connection import DATABASE, engine
from sqlalchemy import text

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT @@VERSION"))
        version_info = result.fetchone()
        
        print("\n=========================================")
        print("KẾT NỐI SQL SERVER THÀNH CÔNG RỰC RỠ!")
        print("=========================================")
        print(f"Phiên bản SQL Server đang dùng:\n{version_info[0]}\n")
        
except Exception as e:
    print("\n KẾT NỐI THẤT BẠI. Lỗi chi tiết:")
    print(e)
    print("\n Hãy kiểm tra lại thông tin SERVER, USER, PASSWORD trong file .env nhé!")