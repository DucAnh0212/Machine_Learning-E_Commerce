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

        # 1. SEED BẢNG USER_VOUCHERS (Người dùng sưu tầm mã)
        print("1. Đang lưu Vouchers vào ví người dùng...")
        user_ids = [u[0] for u in db.execute(text("SELECT UserID FROM Users")).fetchall()]
        voucher_ids = [v[0] for v in db.execute(text("SELECT VoucherID FROM Vouchers WHERE Status = 'Active'")).fetchall()]
        
        user_voucher_data = []
        for uid in random.sample(user_ids, min(3000, len(user_ids))):
            for vid in random.sample(voucher_ids, random.randint(2, 6)):
                user_voucher_data.append({"u": uid, "v": vid, "dt": fake.date_time_between(start_date='-6m', end_date='now')})
        if user_voucher_data:
            db.execute(text("INSERT INTO User_Vouchers (UserID, VoucherID, IsUsed, SavedAt) VALUES (:u, :v, 0, :dt)"), user_voucher_data)
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

        print(">>> HOÀN TẤT PHASE 4!")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_phase_4()