# TẠO DATA ĐÁNH GIÁ & HÀNH VI: DỌN CỖ CHO SVD, PCA+KNN VÀ LOGISTIC REGRESSION
import random
import uuid
import json
import os
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import text
from app.core.database_connection import SessionLocal

fake = Faker('vi_VN')

# --- TỪ ĐIỂN BOT SPAM ---
SPAM_REVIEWS = ["ok", "tốt", "sp tot", "đẹp", "gud", "như hình", "hàng chuẩn", "10 điểm", "giao nhanh", "xài ổn", "tot", "ok shop", "sp ok", "đẹp nha", "ổn", "hàng đẹp", "đúng mô tả", "sản phẩm tốt", "giao hàng nhanh", "đóng gói cẩn thận", "hàng chất lượng", "đáng tiền", "sản phẩm tuyệt vời", "rất hài lòng", "sản phẩm như hình", "giao hàng nhanh chóng", "đóng gói đẹp", "hàng tốt", "sản phẩm chất lượng", "đáng đồng tiền bát gạo", "giao hàng nhanh, sản phẩm tốt", "đóng gói chắc chắn", "hàng đẹp, giao nhanh"]

# --- TỪ ĐIỂN TỪ KHÓA TÌM KIẾM ĐỦ 9 NGÀNH HÀNG ---
SEARCH_KEYWORDS = {
    'Thời Trang Nam': ['áo thun nam', 'quần jean nam', 'áo sơ mi nam', 'áo khoác nam', 'đồ lót nam', 'quần âu', 'áo polo'],
    'Thời Trang Nữ': ['váy nữ', 'chân váy', 'đầm dáng xòe', 'áo kiểu nữ', 'set đồ nữ', 'đầm dự tiệc', 'áo croptop'],
    'Sắc Đẹp': ['kem chống nắng', 'kcn', 'sữa rửa mặt', 'srm', 'toner', 'nước tẩy trang', 'son môi', 'son dưỡng', 'kem dưỡng ẩm', 'nước hoa', 'serum trị mụn'],
    'Máy Tính & Laptop': ['laptop', 'lap top', 'máy tính xách tay', 'laptop sinh viên', 'laptop gaming', 'macbook', 'laptop dell', 'laptop cũ', 'chuột máy tính', 'bàn phím cơ', 'màn hình 24 inch'],
    'Điện Thoại & Phụ Kiện': ['điện thoại', 'đt', 'iphone', 'samsung', 'ốp lưng', 'sạc dự phòng', 'tai nghe nhét tai', 'cáp sạc type c', 'củ sạc nhanh', 'điện thoại giá rẻ'],
    'Thiết Bị Điện Gia Dụng': ['nồi chiên không dầu', 'tủ lạnh', 'máy giặt', 'quạt trần', 'quạt máy', 'bếp từ', 'lò vi sóng', 'máy sấy tóc', 'máy lọc không khí'],
    'Thiết Bị Điện Tử': ['tivi', 'tv', 'tai nghe bluetooth', 'loa bluetooth', 'loa kéo', 'máy chơi game', 'ps5', 'âm ly', 'tay cầm chơi game'],
    'Phụ Kiện Thông Minh': ['đồng hồ thông minh', 'smartwatch', 'vòng đeo tay', 'apple watch', 'đồng hồ nam', 'đồng hồ nữ', 'dây da đồng hồ'],
    'Thể thao': ['giày thể thao', 'quần áo chạy bộ', 'đồ gym', 'túi thể thao', 'giày đá bóng', 'bóng rổ', 'vợt cầu lông', 'thảm yoga', 'bình nước thể thao', 'kính bơi']
}

def load_real_reviews():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'shopee_reviews.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] KHÔNG TÌM THẤY shopee_reviews.json! Hãy đảm bảo file nằm cùng thư mục scripts.")
        return {}

def get_review_from_json(reviews_dict, main_cat_vn, product_name, rating):
    if not reviews_dict: return "Sản phẩm tốt." 
    json_key = "Thiết Bị Điện Tử" 
    name_lower = str(product_name).lower()
    
    if main_cat_vn == 'Thời Trang':
        if any(k in name_lower for k in ['nữ', 'váy', 'chân váy', 'đầm', 'bra']):
            json_key = "Thời Trang Nữ"
        else:
            json_key = "Thời Trang Nam"
    elif main_cat_vn == 'Sắc Đẹp': json_key = "Sắc Đẹp"
    elif main_cat_vn == 'Máy Tính & Laptop': json_key = "Máy Tính & Laptop"
    elif main_cat_vn == 'Điện Thoại & Phụ Kiện': json_key = "Điện Thoại & Phụ Kiện"
    elif main_cat_vn == 'Thiết Bị Điện Gia Dụng': json_key = "Thiết Bị Điện Gia Dụng"
    elif main_cat_vn in ['Thiết Bị Điện Tử', 'Phụ Kiện Thông Minh']: json_key = "Thiết Bị Điện Tử"
    elif main_cat_vn == 'Thể thao': json_key = "Thể thao"
    
    if json_key not in reviews_dict:
        json_key = list(reviews_dict.keys())[0]
        
    rating_str = str(rating)
    if rating_str in reviews_dict[json_key] and len(reviews_dict[json_key][rating_str]) > 0:
        return random.choice(reviews_dict[json_key][rating_str])
    return "Đánh giá tạm ổn."

def run_phase_3():
    db = SessionLocal()
    real_reviews_dict = load_real_reviews()
    if not real_reviews_dict: return

    try:
        db.execute(text("DELETE FROM Review_Metas; DELETE FROM Reviews; DELETE FROM Payment_Methods; DELETE FROM Order_Items; DELETE FROM Orders; DELETE FROM User_Activities; DELETE FROM Search_History;"))
        db.commit()

        users = db.execute(text("SELECT UserID FROM Users")).fetchall()
        user_ids = [u[0] for u in users]
        
        addresses = db.execute(text("SELECT AddressID, UserID FROM Addresses")).fetchall()
        user_address_map = {a[1]: a[0] for a in addresses}
        
        variants_raw = db.execute(text("""
            SELECT v.VariantID, p.ProductID, p.ShopID, v.Price, p.ProductName, c.CategoryName 
            FROM Product_Variants v
            JOIN Products p ON v.ProductID = p.ProductID
            JOIN Product_Categories_Map pcm ON p.ProductID = pcm.ProductID
            JOIN Categories c ON pcm.CategoryID = c.CategoryID
            WHERE c.CategoryName IN ('Thời Trang', 'Sắc Đẹp', 'Máy Tính & Laptop', 'Điện Thoại & Phụ Kiện', 'Thiết Bị Điện Gia Dụng', 'Thiết Bị Điện Tử', 'Phụ Kiện Thông Minh', 'Thể thao')
        """)).fetchall()

        tech_variants, fashion_variants, home_variants, sports_variants, all_variants = [], [], [], [], []
        variants_by_shop = {} 

        for v in variants_raw:
            v_info = {'vid': v[0], 'pid': v[1], 'sid': v[2], 'price': float(v[3]), 'name': v[4], 'cat': v[5]}
            all_variants.append(v_info)
            variants_by_shop.setdefault(v[2], []).append(v_info)

            if v[5] in ['Máy Tính & Laptop', 'Điện Thoại & Phụ Kiện', 'Thiết Bị Điện Tử', 'Phụ Kiện Thông Minh']:
                tech_variants.append(v_info)
            elif v[5] in ['Thời Trang', 'Sắc Đẹp']:
                fashion_variants.append(v_info)
            elif v[5] in ['Thiết Bị Điện Gia Dụng']:
                home_variants.append(v_info)
            elif v[5] == 'Thể thao':
                sports_variants.append(v_info)

        real_users = random.sample(user_ids, int(len(user_ids) * 0.8))
        spam_users = list(set(user_ids) - set(real_users))

        random.shuffle(real_users)
        tech_lovers = real_users[:int(len(real_users) * 0.30)]
        fashion_lovers = real_users[int(len(real_users) * 0.30):int(len(real_users) * 0.60)]
        home_lovers = real_users[int(len(real_users) * 0.60):int(len(real_users) * 0.85)]
        sports_lovers = real_users[int(len(real_users) * 0.85):]
        
        spam_ips = [fake.ipv4() for _ in range(30)] 
        spam_devices = [str(uuid.uuid4()) for _ in range(30)]

        total_orders = 30000
        start_date = datetime.now() - timedelta(days=365)
        all_cat_keys = list(SEARCH_KEYWORDS.keys())

        for i in range(total_orders):
            buyer_id = random.choice(user_ids)
            address_id = user_address_map.get(buyer_id)
            if not address_id: continue

            target_variant = None
            rating_bias = 0
            is_spam = False

            if buyer_id in spam_users:
                target_variant = random.choice(all_variants)
                is_spam = True
            elif buyer_id in tech_lovers:
                target_variant = random.choice(tech_variants if tech_variants and random.random() < 0.8 else all_variants)
                rating_bias = 1 if target_variant in tech_variants else -1
            elif buyer_id in fashion_lovers:
                target_variant = random.choice(fashion_variants if fashion_variants and random.random() < 0.8 else all_variants)
                rating_bias = 1 if target_variant in fashion_variants else -1
            elif buyer_id in sports_lovers:
                target_variant = random.choice(sports_variants if sports_variants and random.random() < 0.8 else all_variants)
                rating_bias = 1 if target_variant in sports_variants else -1
            else:
                target_variant = random.choice(home_variants if home_variants and random.random() < 0.8 else all_variants)
                rating_bias = 1 if target_variant in home_variants else -1

            shop_id = target_variant['sid']
            order_variants = [target_variant]
            
            num_items_in_order = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
            if num_items_in_order > 1:
                shop_inventory = variants_by_shop[shop_id]
                other_items_in_shop = [v for v in shop_inventory if v['vid'] != target_variant['vid']]
                if other_items_in_shop:
                    num_to_add = min(num_items_in_order - 1, len(other_items_in_shop))
                    additional_items = random.sample(other_items_in_shop, num_to_add)
                    order_variants.extend(additional_items)

            order_date = start_date + timedelta(days=random.randint(0, 360), hours=random.randint(0, 23))
            
            # --- 1. SEARCH DẠO ---
            num_searches = random.randint(1, 4)
            session_keywords = []
            actual_cat = target_variant['cat']
            if actual_cat == 'Thời Trang': actual_cat = random.choice(['Thời Trang Nam', 'Thời Trang Nữ'])
            
            target_kw = random.choice(SEARCH_KEYWORDS.get(actual_cat, [target_variant['cat'].lower()]))
            session_keywords.append(target_kw)

            for _ in range(num_searches - 1):
                random_cat = random.choice(all_cat_keys)
                random_kw = random.choice(SEARCH_KEYWORDS[random_cat])
                session_keywords.append(random_kw)

            random.shuffle(session_keywords)
            for idx, kw in enumerate(session_keywords):
                search_time = order_date - timedelta(hours=2) + timedelta(minutes=random.randint(5, 15) * idx)
                db.execute(text("INSERT INTO Search_History (UserID, Keyword, CreatedAt) VALUES (:u, :k, :d)"), 
                           {"u": buyer_id, "k": kw, "d": search_time})
            
            # --- 2. XEM NHƯNG KHÔNG MUA ---
            num_views = random.randint(3, 8)
            viewed_products = random.sample(all_variants, num_views)
            for vp in viewed_products:
                view_time = order_date - timedelta(minutes=random.randint(20, 100))
                db.execute(text("INSERT INTO User_Activities (UserID, ProductID, ActionType, Timestamp) VALUES (:u, :p, 'View', :d)"), 
                           {"u": buyer_id, "p": vp['pid'], "d": view_time})
                if random.random() < 0.15:
                    cart_time = view_time + timedelta(minutes=random.randint(1, 5))
                    db.execute(text("INSERT INTO User_Activities (UserID, ProductID, ActionType, Timestamp) VALUES (:u, :p, 'AddToCart', :d)"), 
                               {"u": buyer_id, "p": vp['pid'], "d": cart_time})

            # --- 3. TẠO ORDER MẸ ---
            res = db.execute(text("""
                INSERT INTO Orders (BuyerID, ShopID, AddressID, OrderDate, PaymentStatus, ShippingStatus) 
                OUTPUT INSERTED.OrderID VALUES (:b, :s, :a, :od, 'Paid', 'Completed')
            """), {"b": buyer_id, "s": shop_id, "a": address_id, "od": order_date})
            order_id = res.fetchone()[0]

            total_amount = 0

            # --- 4. TẠO CÁC ORDER ITEMS VÀ ĐÁNH GIÁ ---
            for ov in order_variants:
                db.execute(text("INSERT INTO User_Activities (UserID, ProductID, ActionType, Timestamp) VALUES (:u, :p, 'View', :d)"), 
                           {"u": buyer_id, "p": ov['pid'], "d": order_date - timedelta(minutes=10)})
                db.execute(text("INSERT INTO User_Activities (UserID, ProductID, ActionType, Timestamp) VALUES (:u, :p, 'AddToCart', :d)"), 
                           {"u": buyer_id, "p": ov['pid'], "d": order_date - timedelta(minutes=2)})

                qty = random.randint(1, 2)
                price = ov['price']
                total_amount += qty * price

                res_item = db.execute(text("""
                    INSERT INTO Order_Items (OrderID, VariantID, Quantity, Price) 
                    OUTPUT INSERTED.OrderItemID VALUES (:o, :v, :q, :p)
                """), {"o": order_id, "v": ov['vid'], "q": qty, "p": price})
                order_item_id = res_item.fetchone()[0]

                if is_spam:
                    final_rating = 5
                    review_comment = random.choice(SPAM_REVIEWS)
                    review_ip = random.choice(spam_ips) 
                    review_device = random.choice(spam_devices)
                else:
                    base_rating = random.choices([5, 4, 3, 2, 1], weights=[40, 30, 15, 10, 5], k=1)[0]
                    final_rating = max(1, min(5, base_rating + rating_bias))
                    review_comment = get_review_from_json(real_reviews_dict, ov['cat'], ov['name'], final_rating)
                    review_ip = fake.ipv4() 
                    review_device = str(uuid.uuid4())

                res_review = db.execute(text("""
                    INSERT INTO Reviews (ProductID, UserID, OrderItemID, Rating, Comment, ReviewDate, IsFake) 
                    OUTPUT INSERTED.ReviewID VALUES (:p, :u, :oi, :r, :c, :rd, :f)
                """), {"p": ov['pid'], "u": buyer_id, "oi": order_item_id, "r": final_rating, "c": review_comment, "rd": order_date + timedelta(days=2), "f": 1 if is_spam else 0})
                review_id = res_review.fetchone()[0]

                db.execute(text("INSERT INTO Review_Metas (ReviewID, IP_Address, DeviceID) VALUES (:r, :ip, :d)"), 
                           {"r": review_id, "ip": review_ip, "d": review_device})

            # --- 5. TẠO THANH TOÁN ---
            db.execute(text("INSERT INTO Payment_Methods (OrderID, Method, PaymentDate, Amount) VALUES (:o, :m, :pd, :a)"), 
                       {"o": order_id, "m": random.choice(['COD', 'VNPay']), "pd": order_date, "a": total_amount})

            if (i + 1) % 1000 == 0:
                db.commit()

        db.commit()
    except Exception as e:
        db.rollback(); raise e
    finally: 
        print(">>> HOÀN TẤT PHASE 3!")
        db.close()

if __name__ == "__main__":
    run_phase_3()
