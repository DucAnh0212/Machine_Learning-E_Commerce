import random
from datetime import timedelta
from faker import Faker
from sqlalchemy import text
from app.core.database_connection import SessionLocal

fake = Faker('vi_VN')

def run_phase_4():
    db = SessionLocal()
    try:
        print(">>> BẮT ĐẦU PHASE 4: Hoàn thiện dữ liệu Giỏ hàng, Thông báo và Đơn hàng...")

        # 1. SEED BẢNG USER_VOUCHERS 
        print("1. Đang lưu Vouchers vào ví người dùng...")
        user_ids = [u[0] for u in db.execute(text("SELECT UserID FROM Users")).fetchall()]
        voucher_ids = [v[0] for v in db.execute(text("SELECT VoucherID FROM Vouchers WHERE Status = 'Active'")).fetchall()]
        
        user_voucher_data = []
        for uid in random.sample(user_ids, min(3000, len(user_ids))):
            for vid in random.sample(voucher_ids, random.randint(2, 6)):
                user_voucher_data.append({"u": uid, "v": vid, "dt": fake.date_time_between(start_date='-6m', end_date='now')})
        if user_voucher_data:
            for uv in user_voucher_data:
                db.execute(text("""
                    IF NOT EXISTS (SELECT 1 FROM User_Vouchers WHERE UserID = :u AND VoucherID = :v)
                    INSERT INTO User_Vouchers (UserID, VoucherID, IsUsed, SavedAt) VALUES (:u, :v, 0, :dt)
                """), uv)
        db.commit()

        # 2. SEED BẢNG ORDER_VOUCHER (Áp dụng mã chuẩn logic)
        orders = db.execute(text("SELECT OrderID, ShopID FROM Orders")).fetchall()
        
        vouchers_info = db.execute(text("SELECT VoucherID, ShopID, VoucherType FROM Vouchers WHERE Status = 'Active'")).fetchall()
        platform_vouchers = [v[0] for v in vouchers_info if v[2] in ['Platform', 'Shipping']]
        shop_vouchers_dict = {}
        for v in vouchers_info:
            if v[2] == 'Shop' and v[1] is not None:
                shop_vouchers_dict.setdefault(v[1], []).append(v[0])

        order_voucher_data = []
        for order in random.sample(orders, int(len(orders) * 0.4)): 
            order_id = order[0]
            order_shop_id = order[1]
            chosen_voucher_id = None
            
            available_shop_vouchers = shop_vouchers_dict.get(order_shop_id, [])
            if available_shop_vouchers and random.random() < 0.7:
                chosen_voucher_id = random.choice(available_shop_vouchers)
            elif platform_vouchers:
                chosen_voucher_id = random.choice(platform_vouchers)
                
            if chosen_voucher_id:
                order_voucher_data.append({"o": order_id, "v": chosen_voucher_id})
                
        if order_voucher_data:
            db.execute(text("INSERT INTO Order_Voucher (OrderID, VoucherID) VALUES (:o, :v)"), order_voucher_data)
        db.commit()

        # 3. SEED BẢNG SHIPPING_UNITS
        orders_date = {o[0]: o[1] for o in db.execute(text("SELECT OrderID, OrderDate FROM Orders")).fetchall()}
        shipping_methods = ['Giao Hàng Nhanh', 'Giao Hàng Tiết Kiệm', 'Viettel Post', 'Shopee Express']
        shipping_data = []
        for oid, o_date in orders_date.items():
            s_date = o_date + timedelta(days=random.randint(1, 2))
            shipping_data.append({
                "o": oid, "m": random.choice(shipping_methods), "f": round(random.uniform(15000, 45000), -3),
                "t": "VN" + str(fake.unique.random_number(digits=10)), "sd": s_date, "dd": s_date + timedelta(days=random.randint(1, 4))
            })
            if len(shipping_data) >= 2000:
                db.execute(text("INSERT INTO Shipping_Units (OrderID, ShippingMethod, ShippingFee, TrackingNumber, ShippedDate, DeliveryDate) VALUES (:o, :m, :f, :t, :sd, :dd)"), shipping_data)
                shipping_data = []
        if shipping_data:
            db.execute(text("INSERT INTO Shipping_Units (OrderID, ShippingMethod, ShippingFee, TrackingNumber, ShippedDate, DeliveryDate) VALUES (:o, :m, :f, :t, :sd, :dd)"), shipping_data)
        db.commit()

        # 4. SEED BẢNG CARTS & CART_ITEMS (ĐÃ SỬA LỖI TÊN BẢNG "CARTS")
        variant_ids = [v[0] for v in db.execute(text("SELECT VariantID FROM Product_Variants")).fetchall()]
        for uid in random.sample(user_ids, min(2000, len(user_ids))):
            # Sửa từ INSERT INTO Cart thành INSERT INTO Carts
            cart_id = db.execute(text("INSERT INTO Carts (UserID) OUTPUT INSERTED.CartID VALUES (:u)"), {"u": uid}).fetchone()[0]
            cart_items = [{"c": cart_id, "v": vid, "q": random.randint(1, 3)} for vid in random.sample(variant_ids, random.randint(1, 5))]
            db.execute(text("INSERT INTO Cart_Items (CartID, VariantID, Quantity) VALUES (:c, :v, :q)"), cart_items)
        db.commit()

        # 5. SEED BẢNG NOTIFICATIONS
        noti_data = []
        shop_ids = list(shop_vouchers_dict.keys())
        for uid in random.sample(user_ids, min(3000, len(user_ids))):
            for _ in range(random.randint(1, 3)):
                noti_data.append({
                    "s": random.choice(shop_ids) if shop_ids and random.random() < 0.5 else None,
                    "r": uid, "t": random.choice(['AI_Recommend', 'OrderUpdate', 'DirectMessage', 'SystemAlert']),
                    "title": "Thông báo hệ thống", "content": "Nội dung thông báo tự động.",
                    "dt": fake.date_time_between(start_date='-1m', end_date='now')
                })
        if noti_data:
            db.execute(text("INSERT INTO Notifications (SenderID, ReceiverID, Type, Title, Content, CreatedAt, IsRead) VALUES (:s, :r, :t, :title, :content, :dt, 0)"), noti_data)
        db.commit()

        # 6. SEED BẢNG REVIEW_REPORTS
        fake_review_ids = [r[0] for r in db.execute(text("SELECT ReviewID FROM Reviews WHERE IsFake = 1")).fetchall()]
        report_data = []
        for rid in random.sample(fake_review_ids, min(800, len(fake_review_ids))):
            for reporter_id in random.sample(user_ids, random.randint(1, 3)):
                report_data.append({"rv": rid, "rp": reporter_id, "rs": "Đánh giá Spam/Fake", "dt": fake.date_time_between(start_date='-2m', end_date='now')})
        if report_data:
            db.execute(text("INSERT INTO Review_Reports (ReviewID, ReporterID, Reason, CreatedAt) VALUES (:rv, :rp, :rs, :dt)"), report_data)
        db.commit()
        
        # 7. CHỐNG FOLLOW ẢO VÀ CẬP NHẬT SHOP FOLLOWER
        print("7. Đang tạo Follower thực tế cho Shop...")
        shop_ids = [s[0] for s in db.execute(text("SELECT ShopID FROM Shops")).fetchall()]
        follow_pairs = set()
        follow_data = []
        for uid in random.sample(user_ids, min(5000, len(user_ids))):
            for sid in random.sample(shop_ids, random.randint(1, 10)):
                if (uid, sid) not in follow_pairs:
                    follow_pairs.add((uid, sid))
                    follow_data.append({"u": uid, "s": sid})
        
        if follow_data:
            db.execute(text("INSERT INTO Shop_Followers (UserID, ShopID) VALUES (:u, :s)"), follow_data)
        
        # Cập nhật số Follower thực tế vào bảng Shops
        db.execute(text("UPDATE Shops SET FollowerCount = (SELECT COUNT(*) FROM Shop_Followers WHERE ShopID = Shops.ShopID)"))
        db.commit()

        print("8. Đang cập nhật Rating cho Sản phẩm và Shop...")
        db.execute(text("""
            UPDATE Products
            SET Rating = ISNULL((SELECT ROUND(AVG(CAST(Rating AS DECIMAL(3,2))), 1) FROM Reviews WHERE ProductID = Products.ProductID), Rating)
        """))
        db.execute(text("""
            UPDATE Shops
            SET Rating = ISNULL((SELECT ROUND(AVG(Rating), 1) FROM Products WHERE ShopID = Shops.ShopID AND Rating > 0), 0.0)
        """))
        db.commit()

        # 9. PHÂN BỔ 8 BẢNG GIAO DIỆN THEO CATEGORY CHÍNH XÁC
        print("9. Đang lọc sản phẩm vào 8 bảng giao diện...")
        
        cats_womens = "('Chân Váy Nữ', 'Đầm Váy Nữ')" 
        cats_mens = "('Áo Khoác Nam', 'Áo Nam', 'Quần Jeans Nam', 'Quần Âu Nam', 'Đồ Lót Nam', 'Trang Sức Nam')"
        cats_beauty = "('Chăm Sóc Da Mặt', 'Tắm & Chăm Sóc Cơ Thể', 'Trang Điểm', 'Nước Hoa', 'Sắc Đẹp')"
        cats_electronics = "('Điện Thoại', 'Máy Tính Bảng', 'Laptop', 'Màn Hình', 'Linh Kiện Máy Tính', 'Máy Tính Bàn', 'Loa', 'Headphone', 'Máy Game Console')"
        cats_sports = "('Giày Thể Thao', 'Quần Áo Thể Thao', 'Phụ Kiện Thể Thao', 'Thể thao')"
        cats_home = "('Đồ Gia Dụng Nhà Bếp', 'Đồ Gia Dụng Lớn', 'Quạt & Máy Nóng Lạnh', 'Bếp Điện', 'Thiết Bị Điện Gia Dụng', 'Điện Máy Gia Đình', 'Quạt & Máy Nóng Lạnh', 'SAMSUNG', 'LG', 'Panasonic')"

        # 1. Bán chạy
        db.execute(text("INSERT INTO UI_Best_Sellers (ProductID) SELECT TOP 50 ProductID FROM Products GROUP BY ProductID ORDER BY NEWID()"))
        
        # 2. Quốc Tế
        db.execute(text("""INSERT INTO UI_International (ProductID) 
            SELECT TOP 50 p.ProductID FROM Products p JOIN Shops s ON p.ShopID = s.ShopID JOIN Addresses a ON s.ShopID = a.UserID
            WHERE a.Province NOT IN ('Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Đồng Nai', 'Bình Dương', 'Bà Rịa - Vũng Tàu', 'Thanh Hóa', 'Nghệ An', 'Thừa Thiên Huế', 'Khánh Hòa', 'Lâm Đồng')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
            
        # 3. Thời trang nữ
        db.execute(text(f"""INSERT INTO UI_Womens_Fashion (ProductID)
            SELECT TOP 50 p.ProductID 
            FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID
            WHERE (c.CategoryName IN {cats_womens}) OR (p.ProductName LIKE '%Women%') OR (p.ProductName LIKE '%Nữ%') OR (p.ProductName LIKE '%Váy%') OR (p.ProductName LIKE '%Đầm%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
            
        # 4. Thời trang nam
        db.execute(text(f"""INSERT INTO UI_Mens_Fashion (ProductID)
            SELECT TOP 50 p.ProductID 
            FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID
            WHERE (c.CategoryName IN {cats_mens}) OR (p.ProductName LIKE '%Men%') OR (p.ProductName LIKE '%Nam%') OR (p.ProductName LIKE '%Polo%') OR (p.ProductName LIKE '%Vest%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
            
        # 5. Làm đẹp
        db.execute(text(f"""INSERT INTO UI_Beauty (ProductID) 
            SELECT TOP 50 p.ProductID FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID 
            WHERE (c.CategoryName IN {cats_beauty}) OR (p.ProductName LIKE '%Beauty%') OR (p.ProductName LIKE '%Skincare%') OR (p.ProductName LIKE '%Lipstick%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
        
        # 6. Đồ điện tử
        db.execute(text(f"""INSERT INTO UI_Electronics (ProductID) 
            SELECT TOP 50 p.ProductID FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID 
            WHERE (c.CategoryName IN {cats_electronics}) OR (p.ProductName LIKE '%Laptop%') OR (p.ProductName LIKE '%Phone%') OR (p.ProductName LIKE '%TV%') OR (p.ProductName LIKE '%Smart%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
        
        # 7. Thể thao
        db.execute(text(f"""INSERT INTO UI_Sports (ProductID) 
            SELECT TOP 50 p.ProductID FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID 
            WHERE (c.CategoryName IN {cats_sports}) OR (p.ProductName LIKE '%Sport%') OR (p.ProductName LIKE '%Shoes%') OR (p.ProductName LIKE '%Sneaker%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
        
        # 8. Đồ gia dụng
        db.execute(text(f"""INSERT INTO UI_Home_Appliances (ProductID) 
            SELECT TOP 50 p.ProductID FROM Products p JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID JOIN Categories c ON pcm.CategoryID = c.CategoryID 
            WHERE (c.CategoryName IN {cats_home}) OR (p.ProductName LIKE '%Appliance%') OR (p.ProductName LIKE '%Fridge%') OR (p.ProductName LIKE '%Washing%')
            GROUP BY p.ProductID ORDER BY NEWID()"""))
        
        db.commit()

        print(">>> HOÀN TẤT PHASE 4!")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_phase_4()
