# TẠO DATA CHO NHỮNG BẢNG ĐỘC LẬP, KHÔNG CÓ FK
import unidecode
from datetime import timedelta
import random
from faker import Faker
from sqlalchemy import text
from passlib.context import CryptContext
from app.core.database_connection import SessionLocal

fake = Faker('vi_VN')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_vn_phone():
    prefixes = ['032', '033', '034', '035', '036', '037', '038', '039', 
                '081', '082', '083', '084', '085', '070', '076', '077', '078', '079', '056', '058', '090', '091', '098']
    return random.choice(prefixes) + ''.join([str(random.randint(0, 9)) for _ in range(7)])

def get_unique_email(full_name, email_counter):
    name_parts = unidecode.unidecode(full_name).lower().split()
    if not name_parts:
        return f"user_{random.randint(1000, 99999)}@gmail.com"
    
    ten = name_parts[-1]
    ho_dem = "".join(name_parts[:-1])
    base_prefix = f"{ten}.{ho_dem}"[:20]
    
    if base_prefix not in email_counter:
        email_counter[base_prefix] = 0
        return f"{base_prefix}@gmail.com"
    else:
        email_counter[base_prefix] += 1
        return f"{base_prefix}{email_counter[base_prefix]}@gmail.com"

def run_phase_1(num_users=15000):
    db = SessionLocal()
    try:
        # 1. BẢNG Roles 
        for role in ["Customer", "Seller", "Admin"]:
            db.execute(text("""
                IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = :r)
                INSERT INTO Roles (RoleName) VALUES (:r)
            """), {"r": role})
        db.commit()
        
        # 2. BẢNG Tags
        raw_tags = [
            "Sale", "New", "Hot", "Limited", "Trending", "Chính hãng", "Hot Trend", "Có Sẵn", 
            #Tag - Thời Trang Nam - Áo Khoác 
            "Chất Liệu Dày Dặn", "Sang Trọng", "Giữ Ấm", "Phong Cách", "Basic", "Dài Tay", "Cao Cấp", 
            #Tag - Thời Trang Nam - Áo 
            "Local Brand", "Unisex", "Cotton", "Form Rộng", "Oversize", "Năng Động", "Thoáng Mát", 
            #Tag - Thời Trang Nam - Quần Jeans
            "Baggy", "Ống Suông", "Chất Vải Dày Dặn", "Đa Dạng Màu Sắc", "Phong Cách", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nam - Quần Dài/Quần Âu 
            "Đứng Form", "Ống Rộng", "Straight", "Trouser", "Hack Dáng", "Co Dãn",
            #Tag - Thời Trang Nam - Đồ Lót
            "mềm mại", "kháng khuẩn", "thấm hút tốt", "Trunk", "Basics", "Thoáng Mát", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nam - Trang Sức Nam
            "Hip Hop", "Bạc", "Titan", "Không Gỉ", "Phong Cách", "Đẳng Cấp", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nữ - Quần 
            "From Xinh", "Tôn Dáng", "Hàn Quốc", "Dáng Rộng", "Dáng Ôm", "Dáng Suông", "Dáng Dài", "Dáng Ngắn", "Dáng Lửng",
            #Tag - Thời Trang Nữ - Chân váy
            "Chân váy", "Dáng Ngắn", "Cá Tính", "Thoải mái", "Thanh Lịch", "Trẻ Trung", 
            #Tag - Thời Trang Nữ - Đầm/Váy
            "Dáng Xòe", "Dáng Dài", "Dáng Ôm", "Dáng Suông", "Đi Tiệc", "Đi Làm", "Đáng Yêu",
            #Tag - Thời Trang Nữ - Đồ lót
            "Không Viền", "Kháng Khuẩn", "Mềm Mịn", "Thoáng Mát", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nữ - Đồ ngủ
            "Dễ Thương", "Đơn Giản", "Thoải Mái", "Mềm Mại", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nữ - Áo
            "Co Giãn", "Dáng Đẹp", "Ôm Body", "Vải Cotton Mịn", "Phong Cách", "Dành Cho Mọi Lứa Tuổi",
            #Tag - Thời Trang Nữ - Áo khoác, Áo choàng & vest 
            "Thoáng Khí", "Thời Trang", "Chống Nắng", "Sang Chảnh", "Dành Cho Mọi Lứa Tuổi", "Đa Dạng Màu Sắc",
            #Tag - Thiết Bị Điện Tử - Loa
            "Bluetooth", "Đa Năng", "Trang Trí", "Sống Động", "Chất Lượng Cao",
            #Tag - Thiết Bị Điện Tử - Tivi
            "Smart Tivi", "Sắc Nét", "4K", "Siêu Mỏng", "Hình Ảnh Chất Lượng Cao", "Độ Sáng Cao",
            #Tag - Thiết Bị Điện Tử - Headphone
            "Giảm tiếng ồn", "Âm thanh tích hợp", "Nhỏ gọn", "Tiện lợi", "Thoải mái", "Đa năng", "Chất lượng âm thanh cao",
            #Tag - Thiết Bị Điện Tử - Máy Game Console
            "Hiện đại", "Hiệu suất cao", "Đa dạng trò chơi", "Cấu hình mạnh mẽ", "Thiết kế đẹp mắt", "Tương thích với nhiều phụ kiện", "Giá cả phải chăng",
            #Tag - Thiết Bị Điện Gia Dụng - Đồ gia dụng nhà bếp 
            "Bền bỉ", "Dễ sử dụng", "Tiết kiệm năng lượng", "Đa chức năng", "Dễ dàng vệ sinh", "Thiết kế hiện đại", "Đáng tin cậy", "An toàn cho gia đình",
            #Tag - Thiết Bị Điện Gia Dụng - Đồ gia dụng lớn
            "Đáng tin cậy", "Tiết kiệm năng lượng", "Đa chức năng", "Tiết kiệm không gian", "Tiết kiệm điện",
            #Tag - Thiết Bị Điện Gia Dụng - Bếp điện
            "Dễ sử dụng", "An toàn", "Dễ dàng vệ sinh", "Nhiệt độ chính xác", "Tiết kiệm năng lượng",
            #Tag - Điện Thoại & Phụ Kiện- Điện thoại
            "Mới", "Đa Dạng Mẫu Mã", "Hiệu Năng Mạnh Mẽ", "Camera Chất Lượng Cao", "Pin Trâu",
            #Tag - Điện Thoại & Phụ Kiện- Máy tính bảng
            "Màn hình lớn", "Pin lâu dài", "Thiết kế mỏng nhẹ", "Đa nhiệm hiệu quả", "Tương thích với nhiều ứng dụng",
            #Tag - Điện Thoại & Phụ Kiện- Pin Dự Phòng
            "Dung lượng lớn", "Sạc nhanh", "Thiết kế nhỏ gọn", "Đa cổng sạc", "Tương thích rộng rãi",
            #Tag - Điện Thoại & Phụ Kiện- Thẻ nhớ
            "Tốc độ cao", "Bảo hành lâu dài", "Đa dung lượng", "Tương thích rộng rãi", "Chống nước, chống sốc",
            #Tag - Điện Thoại & Phụ Kiện- Sim
            "Đa dạng gói cước", "Phủ sóng rộng", "Dịch vụ chăm sóc khách hàng tốt", "Giá cả cạnh tranh",
            #Tag - Máy Tính & Laptop - Máy Tính Bàn 
            "Dễ Nâng Cấp", "Thiết Kế Đẹp", "Hiệu Năng Mạnh Mẽ", "Đa Dạng Cấu Hình", "Giá Cả Phải Chăng",
            #Tag - Máy Tính & Laptop - Màn Hình 
            "Độ Phân Giải Cao", "Màu Sắc Sống Động", "Tần Số Quét Cao", "Góc Nhìn Rộng", "Thiết Kế Mỏng", "Tương Thích Rộng Rãi", "Giá Cả Phải Chăng",
            #Tag - Máy Tính & Laptop - Linh Kiện Máy Tính
            "Dễ Lắp Đặt", "Hiệu Năng Tối Ưu", "Đa Dạng Lựa Chọn", "Tương Thích Rộng Rãi", "Bảo Hành Dài Hạn", "Giá Cả Phải Chăng",
            #Tag - Máy Tính & Laptop - Laptop
            "Dễ dàng Mang Theo", "Dễ dàng tương thích với nhiều phần mềm", "Đa dạng cấu hình", "Hiệu năng mạnh mẽ", "Thời lượng pin lâu dài", "Thiết kế đẹp mắt", "Giá cả phải chăng",
            #Tag - Máy Tính & Laptop - Phụ Kiện Máy Tính
            "Đa Dạng Loại Phụ Kiện", "Thiết Kế Thông Minh", "Tương Thích Rộng Rãi", "Giá Cả Phải Chăng", "Chất Lượng Đảm Bảo",
            #Tag - Máy Tính & Laptop - Gaming 
            "Thiết Kế Hầm Hố", "Đèn LED RGB", "Tản Nhiệt Hiệu Quả", "Hiệu Năng Mạnh Mẽ", "Đa Dạng Cấu Hình", "Giá Cả Phải Chăng", 
            #Tag - Sắc Đẹp - Chăm sóc da mặt
            "Dưỡng ẩm", "Chống lão hóa", "Làm sáng da", "Kiểm soát dầu", "Chống nắng", "Dành cho da nhạy cảm", "Hỗ trợ trị mụn", "Tẩy tế bào chết", "Dưỡng trắng", "Dưỡng da ban đêm",
            #Tag - Sắc Đẹp - Tắm & chăm sóc cơ thể 
            "Làm mềm da", "Hương thơm dễ chịu", "Che khuyết điểm", "Dưỡng ẩm", "Tẩy tế bào chết", "Dưỡng trắng da", "Dành cho da nhạy cảm", "Chống nắng", "Dưỡng da ban đêm",
            #Tag - Sắc Đẹp - Trang điểm 
            "Lâu trôi", "Hiệu ứng tự nhiên", "Độ che phủ cao", "Chống nước", "Đa dạng màu sắc", "Dành cho da nhạy cảm", "Dưỡng ẩm", "Kiểm soát dầu", "Chống nắng", "Dưỡng da ban đêm",
            #Tag - Sắc Đẹp - Vệ sinh răng miệng
            "Làm trắng răng", "Chống sâu răng", "Hơi thở thơm mát", "Dành cho răng nhạy cảm", "Bảo vệ nướu", "Tẩy trắng răng", "Dưỡng môi", "Dưỡng miệng",
            #Tag - Sắc Đẹp - Nước hoa 
            "Hương thơm quyến rũ", "Đa dạng mùi hương", "Phù hợp với mọi dịp", "Dành cho cả nam và nữ", "Lâu trôi", "Thiết kế sang trọng", "Giá cả phải chăng",
            #Tag - Thể thao 
            "Chất liệu bền bỉ", "Thoáng khí", "Dễ dàng giặt sạch", "Thiết kế thời trang", "Đa dạng màu sắc", "Phù hợp cho mọi hoạt động thể thao", "Giá cả phải chăng", "Độ bền cao", "Đa dạng kích cỡ", "Dành cho mọi lứa tuổi", "Dễ dàng vận động", "Hỗ trợ hiệu suất thể thao"
        ]
        
        unique_tags = sorted(list(set([t.strip() for t in raw_tags])))
        
        for tag in unique_tags:
            db.execute(text("""
                IF NOT EXISTS (SELECT 1 FROM Tags WHERE TagName = :t)
                INSERT INTO Tags (TagName) VALUES (:t)
            """), {"t": tag})
        db.commit()

        # 3. BẢNG Users
        hashed_pwd = pwd_context.hash("123456")
        email_counter = {}
        batch_limit = 1000 

        user_query = """
            INSERT INTO Users (FullName, Email, PasswordHash, Phone, Birthday, Gender, FollowerCount, CreatedAt, Status, LastLoginDate)
            VALUES (:FullName, :Email, :PasswordHash, :Phone, :Birthday, :Gender, :FollowerCount, :CreatedAt, :Status, :LastLoginDate)
        """

        current_batch = []
        for i in range(num_users):
            full_name = fake.name()
            created_at = fake.date_time_between(start_date='-3y', end_date='now')
            last_login = created_at + timedelta(days=random.randint(1, 30)) if random.random() > 0.1 else None
            
            current_batch.append({
                "FullName": full_name,
                "Email": get_unique_email(full_name, email_counter),
                "PasswordHash": hashed_pwd,
                "Phone": generate_vn_phone(),
                "Birthday": fake.date_of_birth(minimum_age=16, maximum_age=70).strftime("%Y-%m-%d"),
                "Gender": random.choice(['Male', 'Female', 'Other']),
                "FollowerCount": random.randint(0, 50000),
                "CreatedAt": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Status": 'Active',
                "LastLoginDate": last_login.strftime("%Y-%m-%d %H:%M:%S") if last_login else None
            })

            if len(current_batch) >= batch_limit:
                db.execute(text(user_query), current_batch)
                db.commit()
                current_batch = []

        if current_batch:
            db.execute(text(user_query), current_batch)
            db.commit()
            
    except Exception as e:
        db.rollback()
        raise e
    finally:
        print(">>> HOÀN TẤT PHASE 1!")
        db.close()

if __name__ == "__main__":
    run_phase_1(num_users=10000)
