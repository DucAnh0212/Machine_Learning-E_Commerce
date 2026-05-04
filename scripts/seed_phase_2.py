# TẠO DATA LIÊN KẾT: TỰ ĐỘNG DỊCH TIẾNG ANH (CSV) SANG TIẾNG VIỆT & MAPPING TAG THÔNG MINH
import csv
import random
import os
import re
import itertools
import unidecode
from datetime import timedelta
from faker import Faker
from sqlalchemy import text
from app.core.database_connection import SessionLocal

fake = Faker('vi_VN')

# --- DANH SÁCH ĐỊA CHỈ NỘI ĐỊA ---
DANH_SACH_TINH = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Đồng Nai", "Bình Dương", "Bà Rịa - Vũng Tàu", "Thanh Hóa", "Nghệ An", "Thừa Thiên Huế", "Khánh Hòa", "Lâm Đồng"]
DANH_SACH_DUONG = ["Nguyễn Trãi", "Lê Lợi", "Trần Hưng Đạo", "Hai Bà Trưng", "Lý Thường Kiệt", "Phan Đình Phùng", "Trường Chinh", "Âu Cơ", "Lạc Long Quân", "Giải Phóng", "Xã Đàn", "Tôn Đức Thắng"]

# --- DANH SÁCH ĐỊA CHỈ QUỐC TẾ (CROSS-BORDER) ---
FOREIGN_ADDRESSES = [
    {"pv": "Quảng Đông, Trung Quốc", "dt": "Thâm Quyến", "w": "Khu Nam Sơn", "da": "Tòa nhà Công nghệ cao, Số "},
    {"pv": "Quảng Tây, Trung Quốc", "dt": "Bằng Tường", "w": "Khu Thương Mại Tự Do", "da": "Kho ngoại quan số "},
    {"pv": "Seoul, Hàn Quốc", "dt": "Gangnam-gu", "w": "Yeoksam-dong", "da": "Teheran-ro, Tòa nhà "},
    {"pv": "Tokyo, Nhật Bản", "dt": "Shibuya", "w": "Jingumae", "da": "Phố Takeshita, Số "},
    {"pv": "California, Mỹ", "dt": "City of Industry", "w": "San Gabriel Valley", "da": "Kho trung chuyển Amazon, Block "},
    {"pv": "Đài Bắc, Đài Loan", "dt": "Tân Bắc", "w": "Bản Kiều", "da": "Đường Trung Chính, Kho "},
    {"pv": "Bangkok, Thái Lan", "dt": "Chatuchak", "w": "Lat Yao", "da": "Khu chợ sỉ quần áo, Quầy "}
]

# --- TỪ ĐIỂN DỊCH & MAPPING ---
MAIN_CAT_TRANSLATE = {
    'Fashion': 'Thời Trang', 'Skincare': 'Sắc Đẹp', 'Laptops': 'Máy Tính & Laptop',
    'Mobiles': 'Điện Thoại & Phụ Kiện', 'Appliances': 'Thiết Bị Điện Gia Dụng',
    'Televisions': 'Thiết Bị Điện Tử', 'Wearables': 'Phụ Kiện Thông Minh', 'Electronics': 'Thiết Bị Điện Tử',
    'Sports': 'Thể thao' 
}

CATEGORY_MAPPING = {
    'Fashion': ['Áo Khoác Nam', 'Áo Nam', 'Quần Jeans Nam', 'Quần Âu Nam', 'Đồ Lót Nam', 'Chân Váy Nữ', 'Đầm Váy Nữ'],
    'Skincare': ['Chăm Sóc Da Mặt', 'Tắm & Chăm Sóc Cơ Thể', 'Trang Điểm', 'Nước Hoa'],
    'Laptops': ['Laptop', 'Màn Hình', 'Linh Kiện Máy Tính', 'Máy Tính Bàn'],
    'Mobiles': ['Điện Thoại', 'Máy Tính Bảng', 'Pin Dự Phòng', 'Thẻ Nhớ'],
    'Appliances': ['Đồ Gia Dụng Nhà Bếp', 'Đồ Gia Dụng Lớn', 'Quạt & Máy Nóng Lạnh', 'Bếp Điện'],
    'Televisions': ['Tivi'],
    'Wearables': ['Vớ/Tất', 'Trang Sức Nam'],
    'Electronics': ['Loa', 'Headphone', 'Máy Game Console'],
    'Sports': ['Giày Thể Thao', 'Quần Áo Thể Thao', 'Phụ Kiện Thể Thao']
}

SPECIFIC_TAG_MAP = {
    'Áo Khoác Nam': ["Chất Liệu Dày Dặn", "Sang Trọng", "Giữ Ấm", "Phong Cách", "Basic", "Dài Tay", "Cao Cấp"],
    'Áo Nam': ["Local Brand", "Unisex", "Cotton", "Form Rộng", "Oversize", "Năng Động", "Thoáng Mát"],
    'Quần Jeans Nam': ["Baggy", "Ống Suông", "Chất Vải Dày Dặn", "Đa Dạng Màu Sắc", "Phong Cách"],
    'Quần Âu Nam': ["Đứng Form", "Ống Rộng", "Straight", "Trouser", "Hack Dáng", "Co Dãn"],
    'Đồ Lót Nam': ["mềm mại", "kháng khuẩn", "thấm hút tốt", "Trunk", "Basics", "Thoáng Mát"],
    'Chân Váy Nữ': ["Chân váy", "Dáng Ngắn", "Cá Tính", "Thoải mái", "Thanh Lịch", "Trẻ Trung"],
    'Đầm Váy Nữ': ["Dáng Xòe", "Dáng Dài", "Dáng Ôm", "Dáng Suông", "Đi Tiệc", "Đi Làm", "Đáng Yêu"],
    'Trang Sức Nam': ["Hip Hop", "Bạc", "Titan", "Không Gỉ", "Phong Cách", "Đẳng Cấp"],
    'Vớ/Tất': ["Dày Dặn", "Thoáng Mát", "Chống Trơn Trượt", "Thấm Hút Tốt", "Mềm Mại", "Co Dãn"],
    'Laptop': ["Dễ dàng Mang Theo", "Hiệu năng mạnh mẽ", "Thời lượng pin lâu dài", "Thiết kế đẹp mắt"],
    'Máy Tính Bàn': ["Dễ Nâng Cấp", "Thiết Kế Đẹp", "Hiệu Năng Mạnh Mẽ", "Đa Dạng Cấu Hình"],
    'Màn Hình': ["Độ Phân Giải Cao", "Màu Sắc Sống Động", "Tần Số Quét Cao", "Góc Nhìn Rộng"],
    'Linh Kiện Máy Tính': ["Dễ Lắp Đặt", "Hiệu Năng Tối Ưu", "Đa Dạng Lựa Chọn", "Bảo Hành Dài Hạn"],
    'Điện Thoại': ["Mới", "Đa Dạng Mẫu Mã", "Hiệu Năng Mạnh Mẽ", "Camera Chất Lượng Cao", "Pin Trâu"],
    'Máy Tính Bảng': ["Màn hình lớn", "Pin lâu dài", "Thiết kế mỏng nhẹ", "Đa nhiệm hiệu quả"],
    'Pin Dự Phòng': ["Dung lượng lớn", "Sạc nhanh", "Thiết kế nhỏ gọn", "Đa cổng sạc"],
    'Thẻ Nhớ': ["Tốc độ cao", "Bảo hành lâu dài", "Đa dung lượng", "Chống nước, chống sốc"],
    'Đồ Gia Dụng Nhà Bếp': ["Bền bỉ", "Dễ sử dụng", "Tiết kiệm năng lượng", "Đa chức năng"],
    'Đồ Gia Dụng Lớn': ["Đáng tin cậy", "Tiết kiệm năng lượng", "Đa chức năng", "Tiết kiệm không gian"],
    'Bếp Điện': ["Dễ sử dụng", "An toàn", "Nhiệt độ chính xác", "Tiết kiệm năng lượng"],
    'Quạt & Máy Nóng Lạnh': ["Tiết kiệm năng lượng", "Đa chức năng", "Thiết kế hiện đại", "Bảo hành lâu dài"],
    'Tivi': ["Smart Tivi", "Sắc Nét", "4K", "Siêu Mỏng", "Hình Ảnh Chất Lượng Cao", "Độ Sáng Cao"],
    'Loa': ["Bluetooth", "Đa Năng", "Trang Trí", "Sống Động", "Chất Lượng Cao"],
    'Headphone': ["Giảm tiếng ồn", "Âm thanh tích hợp", "Nhỏ gọn", "Tiện lợi", "Thoải mái"],
    'Máy Game Console': ["Hiện đại", "Hiệu suất cao", "Đa dạng trò chơi", "Cấu hình mạnh mẽ"],
    'Chăm Sóc Da Mặt': ["Dưỡng ẩm", "Chống lão hóa", "Làm sáng da", "Kiểm soát dầu", "Chống nắng"],
    'Tắm & Chăm Sóc Cơ Thể': ["Làm mềm da", "Hương thơm dễ chịu", "Che khuyết điểm", "Dưỡng ẩm"],
    'Trang Điểm': ["Lâu trôi", "Hiệu ứng tự nhiên", "Độ che phủ cao", "Chống nước", "Đa dạng màu sắc"],
    'Nước Hoa': ["Hương thơm quyến rũ", "Đa dạng mùi hương", "Phù hợp với mọi dịp", "Lâu trôi"],
    'Giày Thể Thao': ["Chất liệu bền bỉ", "Thoáng khí", "Độ bền cao", "Dễ dàng vận động", "Hỗ trợ hiệu suất thể thao", "Thiết kế thời trang"],
    'Quần Áo Thể Thao': ["Thoáng khí", "Dễ dàng giặt sạch", "Thiết kế thời trang", "Đa dạng màu sắc", "Dễ dàng vận động"],
    'Phụ Kiện Thể Thao': ["Chất liệu bền bỉ", "Giá cả phải chăng", "Phù hợp cho mọi hoạt động thể thao", "Đa dạng kích cỡ"]
}

ENRICHED_DESC = {
    'Skincare': [
        "Giúp da căng bóng, mịn màng chỉ sau 7 ngày sử dụng liên tục.", "Phù hợp với mọi loại da, kể cả làn da nhạy cảm nhất.", "Chiết xuất hoàn toàn tự nhiên, không chứa paraben.", "Công thức mỏng nhẹ, thẩm thấu nhanh vào da không gây bết dính.", "Bảo vệ da toàn diện dưới tác động của tia UV.", "Nuôi dưỡng làn da từ sâu bên trong, ngăn ngừa lão hóa.", "Cấp ẩm tức thì, mang lại cảm giác tươi mát.", "Thành phần an toàn, được các bác sĩ da liễu khuyên dùng.", "Đánh bay quầng thâm và nếp nhăn vùng mắt hiệu quả.", "Khôi phục hàng rào bảo vệ tự nhiên của da.", "Làm sạch sâu lỗ chân lông, ngăn ngừa mụn hình thành.", "Hương thơm dịu nhẹ, mang lại cảm giác thư giãn khi sử dụng.", "Cải thiện độ đàn hồi, giúp da săn chắc hơn.", "Dưỡng trắng an toàn, mờ thâm nám tàn nhang.", "Sản phẩm thuần chay, không thử nghiệm trên động vật.", "Tái tạo tế bào da mới trong lúc bạn ngủ.", "Kiểm soát bã nhờn cực tốt cho những ngày hè oi bức.", "Lớp finish mỏng nhẹ, có thể dùng làm lớp lót trang điểm.", "Xóa mờ các vết thâm do mụn để lại.", "Cung cấp vitamin thiết yếu cho một làn da khỏe mạnh."
    ],
    'Fashion': [
        "Chất liệu vải cao cấp, thấm hút mồ hôi cực tốt.", "Thiết kế thời thượng, chuẩn form tôn dáng.", "Đường may tinh tế, tỉ mỉ đến từng chi tiết nhỏ.", "Dễ dàng phối hợp với nhiều phong cách khác nhau.", "Chất vải mềm mịn, không xù lông sau nhiều lần giặt.", "Họa tiết in sắc nét, không bong tróc theo thời gian.", "Mang lại sự thoải mái tối đa cho người mặc.", "Phù hợp mặc đi làm, đi chơi hay dự tiệc.", "Sản phẩm được thiết kế độc quyền, dẫn đầu xu hướng.", "Màu sắc nhã nhặn, không bị phai màu khi giặt.", "Kiểu dáng basic nhưng không bao giờ lỗi mốt.", "Vải co giãn 4 chiều, giúp bạn tự do vận động.", "Lớp lót bên trong êm ái, thân thiện với làn da.", "Che khuyết điểm cơ thể một cách hoàn hảo.", "Chiếc áo không thể thiếu trong tủ đồ của bạn.", "Thân thiện với môi trường, sử dụng thuốc nhuộm an toàn.", "Thiết kế cổ bẻ thanh lịch, lịch sự.", "Lên dáng cực chuẩn, đúng kích thước mô tả.", "Sự lựa chọn hoàn hảo cho những ngày dạo phố.", "Phong cách tối giản tinh tế (Minimalism)."
    ],
    'Laptops': [
        "Hiệu năng vượt trội, xử lý mượt mà mọi tác vụ nặng.", "Màn hình độ phân giải cao, hiển thị màu sắc sống động.", "Thiết kế mỏng nhẹ, dễ dàng mang theo mọi lúc mọi nơi.", "Thời lượng pin cực trâu, đáp ứng cả ngày dài làm việc.", "Bàn phím gõ êm ái, hành trình phím sâu.", "Hệ thống tản nhiệt tiên tiến, máy luôn mát mẻ.", "Card đồ họa rời mạnh mẽ, chiến game không giật lag.", "Bảo mật vân tay và nhận diện khuôn mặt an toàn.", "Tích hợp đa dạng cổng kết nối hiện đại.", "Khung viền kim loại sang trọng và chắc chắn.", "Ổ cứng SSD tốc độ cao, khởi động chỉ trong vài giây.", "Hỗ trợ sạc nhanh, tiết kiệm thời gian chờ đợi.", "Màn hình viền siêu mỏng, tối đa không gian hiển thị.", "Âm thanh vòm chất lượng cao, giải trí đỉnh cao.", "Touchpad đa điểm, phản hồi cực kỳ chính xác.", "Bản lề chắc chắn, mở gập mượt mà.", "Tích hợp sẵn Windows bản quyền mới nhất.", "Bảo hành chính hãng 24 tháng toàn cầu.", "Đạt tiêu chuẩn độ bền quân đội Mỹ.", "Webcam độ nét cao, hỗ trợ họp trực tuyến hoàn hảo."
    ],
    'Mobiles': [
        "Cụm camera sắc nét, chụp đêm cực kỳ ấn tượng.", "Hiệu năng mạnh mẽ với con chip thế hệ mới nhất.", "Màn hình OLED tần số quét 120Hz siêu mượt.", "Dung lượng pin khủng, hỗ trợ sạc siêu nhanh.", "Thiết kế nguyên khối, khung viền kim loại sang trọng.", "Hỗ trợ kết nối 5G tốc độ cực cao.", "Khả năng chống nước và chống bụi tiêu chuẩn IP68.", "Mặt kính cường lực thế hệ mới chống trầy xước.", "Giao diện hệ điều hành tối ưu, dễ sử dụng.", "Loa kép stereo âm thanh sống động.", "Chụp ảnh chân dung xóa phông chuyên nghiệp.", "Bộ nhớ trong dung lượng lớn, lưu trữ thoải mái.", "Màu sắc mặt lưng độc đáo, thay đổi theo góc nhìn.", "Cảm biến vân tay dưới màn hình nhạy bén.", "Khả năng quay video 4K siêu chống rung.", "Trọng lượng nhẹ, cầm nắm thoải mái bằng một tay.", "Tích hợp công nghệ AI thông minh tối ưu pin.", "Sạc ngược không dây vô cùng tiện lợi.", "Đèn flash LED kép trợ sáng hoàn hảo.", "Hỗ trợ 2 sim 2 sóng vật lý tiện dụng."
    ],
    'Appliances': [
        "Công nghệ Inverter siêu tiết kiệm điện năng.", "Độ bền cực cao, hoạt động êm ái không tiếng ồn.", "Thiết kế hiện đại, tối ưu không gian sống.", "Màn hình LED hiển thị nhiệt độ/chế độ rõ ràng.", "Chất liệu vỏ ngoài cao cấp, dễ dàng lau chùi.", "Tích hợp nhiều chế độ tự động thông minh.", "Khả năng làm lạnh/làm nóng siêu tốc.", "Bảo vệ an toàn tự ngắt khi quá tải.", "Công nghệ khử mùi và kháng khuẩn tiên tiến.", "Dung tích lớn, phù hợp cho gia đình đông người.", "Lưới lọc dễ dàng tháo lắp và vệ sinh.", "Điều khiển từ xa qua ứng dụng trên điện thoại.", "Thiết kế nhỏ gọn, dễ dàng di chuyển.", "Bảng điều khiển cảm ứng một chạm tiện lợi.", "Khóa trẻ em an toàn tuyệt đối.", "Cửa kính cường lực chịu nhiệt cao cấp.", "Chức năng hẹn giờ thông minh lên đến 24h.", "Thiết kế sang trọng, nâng tầm đẳng cấp ngôi nhà.", "Vật liệu lồng giặt/nồi nấu bằng thép không gỉ.", "Được chứng nhận nhãn năng lượng 5 sao."
    ],
    'Televisions': [
        "Độ phân giải 4K siêu nét, chi tiết đến từng điểm ảnh.", "Màu sắc sống động với công nghệ chấm lượng tử.", "Thiết kế tràn viền, mang lại trải nghiệm xem đắm chìm.", "Âm thanh vòm Dolby Atmos chuẩn rạp chiếu phim.", "Hệ điều hành Smart TV mượt mà, kho ứng dụng phong phú.", "Tìm kiếm bằng giọng nói tiếng Việt chính xác.", "Tần số quét cao, xem thể thao và chơi game không bóng mờ.", "Góc nhìn siêu rộng, hình ảnh không bị biến màu.", "Chíp xử lý AI tự động nâng cấp chất lượng hình ảnh.", "Thiết kế siêu mỏng, dễ dàng treo tường như bức tranh.", "Kết nối không dây với điện thoại mượt mà.", "Tích hợp sẵn các ứng dụng giải trí Netflix, YouTube.", "Công nghệ HDR tối ưu độ tương phản hình ảnh.", "Chế độ bảo vệ mắt khi xem trong bóng tối.", "Đa dạng cổng kết nối HDMI, USB, Optical.", "Tự động điều chỉnh độ sáng theo môi trường.", "Loa tích hợp công suất lớn, âm trầm mạnh mẽ.", "Giao diện trực quan, người lớn tuổi cũng dễ dùng.", "Remote thông minh tích hợp phím tắt tiện lợi.", "Bảo hành tận nhà 24 tháng chính hãng."
    ],
    'Wearables': [
        "Theo dõi nhịp tim và SpO2 chính xác 24/7.", "Thiết kế thể thao, năng động và vô cùng nhẹ.", "Chống nước tiêu chuẩn 5ATM, thoải mái bơi lội.", "Thời lượng pin lên đến 14 ngày chỉ với một lần sạc.", "Màn hình AMOLED hiển thị rõ nét dưới trời nắng.", "Tích hợp hàng trăm chế độ tập luyện thể thao chuyên nghiệp.", "Theo dõi chất lượng giấc ngủ và mức độ căng thẳng.", "Nhận thông báo cuộc gọi và tin nhắn trực tiếp.", "Dây đeo silicone mềm mại, không gây kích ứng da.", "Tích hợp GPS độc lập vẽ lại bản đồ chạy bộ.", "Mặt đồng hồ tùy biến đa dạng theo phong cách.", "Theo dõi chu kỳ kinh nguyệt cho phái nữ.", "Chế độ Always On Display tiện lợi.", "Nghe nhạc trực tiếp qua kết nối tai nghe Bluetooth.", "Viền bezel kim loại sang trọng và bền bỉ.", "Đo lượng calo tiêu thụ chính xác sau mỗi buổi tập.", "Cảnh báo nhịp tim bất thường bảo vệ sức khỏe.", "Hỗ trợ đàm thoại trực tiếp trên đồng hồ.", "Cảm biến gia tốc siêu nhạy đếm số bước chân.", "Tích hợp trợ lý ảo nhắc nhở lịch trình hàng ngày."
    ],
    'Electronics': [
        "Chất lượng âm thanh Hi-Res Audio đỉnh cao.", "Công nghệ chống ồn chủ động ANC tiên tiến.", "Thiết kế nhỏ gọn, dễ dàng mang theo khi du lịch.", "Kết nối Bluetooth 5.0 ổn định, độ trễ cực thấp.", "Thời gian phát nhạc liên tục lên đến 20 giờ.", "Âm bass sâu và chắc, dải treble trong trẻo.", "Micro chống ồn, đàm thoại rõ ràng trong môi trường ồn ào.", "Chất liệu hoàn thiện cao cấp, chống trầy xước.", "Khả năng ghép nối nhiều loa cùng lúc để tạo dàn âm thanh.", "Chống nước IPX7, yên tâm sử dụng ngoài trời.", "Đệm tai nghe êm ái, không đau tai khi đeo lâu.", "Tích hợp đèn LED RGB nháy theo điệu nhạc.", "Hỗ trợ điều khiển bằng cảm ứng tiện lợi.", "Sạc nhanh 10 phút cho 2 giờ nghe nhạc.", "Tương thích hoàn hảo với cả iOS và Android.", "Dây cáp bọc dù siêu bền, chống rối chống đứt.", "Jack cắm mạ vàng đảm bảo tín hiệu truyền tải.", "Khả năng kết nối đa thiết bị cùng một lúc.", "Thiết kế công thái học vừa vặn với mọi kích cỡ tai.", "Bảo vệ màng loa bằng lưới thép không gỉ cường lực."
    ],
    'Sports': [
        "Chất liệu vải thể thao chuyên dụng, cực kỳ thoáng khí.", "Thiết kế khí động học, hỗ trợ tối đa hiệu suất vận động.", "Đế giày đàn hồi tốt, giảm thiểu chấn thương khi chạy.", "Khả năng thấm hút mồ hôi và khô nhanh vượt trội.", "Trọng lượng siêu nhẹ, mang lại cảm giác 'như không mang'.", "Lớp đệm êm ái, bảo vệ cổ chân và khớp gối.", "Chất vải co giãn 4 chiều, thoải mái xoạc chân, uốn người.", "Thiết kế chống trơn trượt, bám sân cực kỳ tốt.", "Đường may phẳng (flatlock) không gây ma sát xước da.", "Phù hợp cho cả gym, yoga, chạy bộ và thể thao ngoài trời.", "Màu sắc phản quang, an toàn khi vận động buổi tối.", "Túi ẩn có khóa kéo tiện lợi đựng điện thoại, chìa khóa.", "Khử mùi kháng khuẩn, giữ cơ thể luôn thơm tho sau khi tập.", "Form dáng thể thao tôn lên những đường nét cơ bắp.", "Chất liệu không nhăn, không cần ủi sau khi giặt.", "Dễ dàng vệ sinh, lau chùi vết bẩn bùn đất.", "Tích hợp lưới tản nhiệt ở những vùng ra nhiều mồ hôi.", "Lõi giày đúc nguyên khối, độ bền bỉ đáng kinh ngạc.", "Phụ kiện thể thao đi kèm thông minh, dễ dàng mang theo.", "Được các vận động viên chuyên nghiệp khuyên dùng."
    ]
}

ATTR_MAP = {
    'Fashion': {'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Đen', 'Trắng', 'Xanh Navy', 'Xám', 'Đỏ', 'Xanh Lá', 'Vàng', 'Hồng', 'Tím',  'Cam', 'Be']},
    'Sports': {'sizes': ['S', 'M', 'L', 'XL', 'XXL'], 'colors': ['Đen', 'Trắng', 'Xám', 'Đỏ', 'Xanh Dương', 'Xanh Lá', 'Vàng', 'Hồng', 'Tím']},
    'Laptops': {'sizes': ['8GB RAM', '16GB RAM', '32GB RAM'], 'colors': ['Xám', 'Bạc', 'Đen']},
    'Mobiles': {'sizes': ['128GB', '256GB', '512GB'], 'colors': ['Đen', 'Trắng', 'Titan']},
    'Skincare': {'sizes': ['30ml', '50ml', '100ml'], 'colors': ['Mặc định']},
    'Default': {'sizes': ['Tiêu chuẩn'], 'colors': ['Mặc định']}
}

PRICE_RANGES = {
    'Laptops': (10000000, 45000000),
    'Mobiles': (3000000, 30000000),
    'Televisions': (5000000, 40000000),
    'Appliances': (1000000, 15000000),
    'Fashion': (150000, 1000000),
    'Sports': (150000, 2000000),
    'Skincare': (120000, 1500000),
    'Wearables': (300000, 6000000),
    'Electronics': (200000, 5000000),
    'Default': (100000, 1000000)
}

def clean_desc_conflict(text, cat):
    text = re.sub(r'\d+\s?(GB|RAM|ml|ML|inch|")', '', str(text), flags=re.IGNORECASE)
    return text.strip()

def clean_and_format_desc(text_str, gen_phrase):
    text_str = str(text_str).strip()
    if text_str.startswith("[") and text_str.endswith("]"):
        items = re.findall(r"'(.*?)'|\"(.*?)\"", text_str)
        items = [i[0] or i[1] for i in items if i[0] or i[1]]
        if items:
            text_str = "\n- " + "\n- ".join(items)
    
    text_str = re.sub(r'\s{2,}', ' ', text_str).strip()
    if len(text_str) < 5: return gen_phrase
    return f"{gen_phrase}\n\nThông tin chi tiết:\n{text_str}"

def smart_categorize(product_name, main_cat):
    name_lower = str(product_name).lower()
    
    if main_cat == 'Sports':
        if any(k in name_lower for k in ['shoe', 'sneaker', 'giày', 'footwear']): return 'Giày Thể Thao'
        if any(k in name_lower for k in ['bag', 'bottle', 'phụ kiện', 'túi', 'kính', 'vợt', 'bóng']): return 'Phụ Kiện Thể Thao'
        return 'Quần Áo Thể Thao'
    elif main_cat == 'Mobiles':
        if any(k in name_lower for k in ['cable', 'charger', 'sạc', 'cáp', 'power bank', 'dự phòng', 'adapter']): return 'Pin Dự Phòng'
        if any(k in name_lower for k in ['memory', 'sd', 'thẻ nhớ', 'micro', 'drive']): return 'Thẻ Nhớ'
        if any(k in name_lower for k in ['tablet', 'ipad', 'tab', 'bảng']): return 'Máy Tính Bảng'
        return 'Điện Thoại'
    elif main_cat == 'Laptops':
        if any(k in name_lower for k in ['monitor', 'màn hình', 'display', 'screen']): return 'Màn Hình'
        if any(k in name_lower for k in ['desktop', 'pc', 'bàn', 'tower', 'aio', 'all-in-one']): return 'Máy Tính Bàn'
        if any(k in name_lower for k in ['ram', 'ssd', 'hdd', 'mouse', 'chuột', 'keyboard', 'bàn phím', 'drive', 'cpu', 'motherboard', 'vga']): return 'Linh Kiện Máy Tính'
        return 'Laptop'
    elif main_cat == 'Fashion':
        if any(k in name_lower for k in ['skirt', 'chân váy', 'váy ngắn']): return 'Chân Váy Nữ'
        if any(k in name_lower for k in ['dress', 'đầm', 'váy dài', 'gown']): return 'Đầm Váy Nữ'
        if any(k in name_lower for k in ['jacket', 'khoác', 'coat', 'hoodie', 'sweater', 'blazer']): return 'Áo Khoác Nam'
        if any(k in name_lower for k in ['jeans', 'jean', 'denim']): return 'Quần Jeans Nam'
        if any(k in name_lower for k in ['trouser', 'pants', 'quần', 'short', 'chinos']): return 'Quần Âu Nam'
        if any(k in name_lower for k in ['underwear', 'brief', 'lót', 'panties', 'bra', 'boxer']): return 'Đồ Lót Nam'
        return 'Áo Nam'
    elif main_cat == 'Appliances':
        if any(k in name_lower for k in ['fridge', 'refrigerator', 'washing', 'tủ lạnh', 'máy giặt', 'air conditioner', 'điều hòa', 'freezer']): return 'Đồ Gia Dụng Lớn'
        if any(k in name_lower for k in ['fan', 'quạt', 'heater', 'nóng lạnh', 'purifier']): return 'Quạt & Máy Nóng Lạnh'
        if any(k in name_lower for k in ['stove', 'bếp', 'induction', 'gas', 'microwave', 'oven', 'lò nướng']): return 'Bếp Điện'
        return 'Đồ Gia Dụng Nhà Bếp'
    elif main_cat == 'Skincare':
        if any(k in name_lower for k in ['body', 'bath', 'tắm', 'shower', 'lotion', 'soap', 'xà phòng']): return 'Tắm & Chăm Sóc Cơ Thể'
        if any(k in name_lower for k in ['makeup', 'lipstick', 'foundation', 'mascara', 'trang điểm', 'phấn', 'son', 'concealer']): return 'Trang Điểm'
        if any(k in name_lower for k in ['perfume', 'fragrance', 'cologne', 'nước hoa', 'parfum', 'eau de']): return 'Nước Hoa'
        return 'Chăm Sóc Da Mặt'
    elif main_cat == 'Electronics':
        if any(k in name_lower for k in ['headphone', 'earphone', 'tai nghe', 'earbuds', 'headset', 'airpods']): return 'Headphone'
        if any(k in name_lower for k in ['speaker', 'loa', 'soundbar']): return 'Loa'
        if any(k in name_lower for k in ['console', 'playstation', 'xbox', 'nintendo', 'game', 'controller']): return 'Máy Game Console'
        return 'Thiết Bị Điện Tử' 
    elif main_cat == 'Wearables':
        if any(k in name_lower for k in ['sock', 'tất', 'vớ']): return 'Vớ/Tất'
        if any(k in name_lower for k in ['ring', 'necklace', 'bracelet', 'trang sức', 'watch', 'đồng hồ']): return 'Trang Sức Nam'
        return 'Phụ Kiện Thông Minh'

    return random.choice(CATEGORY_MAPPING.get(main_cat, [MAIN_CAT_TRANSLATE.get(main_cat, main_cat)]))

def get_or_create_category(db, cat_cache, c_name):
    c_name = c_name.strip()
    if c_name in cat_cache: return cat_cache[c_name]
        
    existing = db.execute(text("SELECT CategoryID FROM Categories WHERE CategoryName = :n"), {"n": c_name}).fetchone()
    if existing:
        cat_cache[c_name] = existing[0]
        return existing[0]
        
    try:
        res = db.execute(text("INSERT INTO Categories (CategoryName) OUTPUT INSERTED.CategoryID VALUES (:n)"), {"n": c_name})
        new_id = res.fetchone()[0]
        db.commit()
        cat_cache[c_name] = new_id
        return new_id
    except Exception:
        db.rollback()
        max_id = db.execute(text("SELECT ISNULL(MAX(CategoryID), 0) FROM Categories")).fetchone()[0]
        new_id = max_id + 1
        try:
            db.execute(text("SET IDENTITY_INSERT Categories ON"))
            db.execute(text("INSERT INTO Categories (CategoryID, CategoryName) VALUES (:i, :n)"), {"i": new_id, "n": c_name})
            db.execute(text("SET IDENTITY_INSERT Categories OFF"))
        except:
            db.rollback()
            db.execute(text("INSERT INTO Categories (CategoryID, CategoryName) VALUES (:i, :n)"), {"i": new_id, "n": c_name})
        db.commit()
        cat_cache[c_name] = new_id
        return new_id

def sanitize_sku_part(text_str):
    if not text_str: return "UNK"
    clean_str = unidecode.unidecode(str(text_str)).upper()
    clean_str = re.sub(r'[^A-Z0-9]', '', clean_str)
    return clean_str[:6]

def run_phase_2():
    db = SessionLocal()
    try:
        
        tables = ['Categories', 'Products', 'Product_Variants', 'Product_Images', 'Shops', 'Addresses', 'Tags']
        for t in tables:
            try:
                db.execute(text(f"DBCC CHECKIDENT ('{t}')"))
                db.commit()
            except:
                db.rollback()
        
        user_data = db.execute(text("SELECT UserID, Phone, FullName FROM Users")).fetchall()
        user_info_map = {r[0]: {"phone": r[1], "name": r[2]} for r in user_data}
        user_ids = list(user_info_map.keys())
        role_map = {r[1]: r[0] for r in db.execute(text("SELECT RoleID, RoleName FROM Roles")).fetchall()}
        tag_data = db.execute(text("SELECT TagID, TagName FROM Tags")).fetchall()
        
        if not user_ids:
            return

        seller_ids = random.sample(user_ids, int(len(user_ids) * 0.1))
        shop_specialized_map = {} 
        main_cats_list = list(MAIN_CAT_TRANSLATE.keys())

        # Tạo Shop
        for uid in user_ids:
            db.execute(text("""
                IF NOT EXISTS (SELECT 1 FROM User_Roles WHERE UserID = :u AND RoleID = :r)
                INSERT INTO User_Roles (UserID, RoleID) VALUES (:u, :r)
            """), {"u": uid, "r": role_map['Customer']})
            
            if uid in seller_ids:
                assigned_cat = random.choice(main_cats_list)
                shop_specialized_map[uid] = assigned_cat
                db.execute(text("""
                    IF NOT EXISTS (SELECT 1 FROM User_Roles WHERE UserID = :u AND RoleID = :r)
                    INSERT INTO User_Roles (UserID, RoleID) VALUES (:u, :r)
                """), {"u": uid, "r": role_map['Seller']})
                
                vn_cat_name = MAIN_CAT_TRANSLATE[assigned_cat]
                db.execute(text("IF NOT EXISTS (SELECT 1 FROM Shops WHERE ShopID = :s) INSERT INTO Shops (ShopID, ShopName, Description, Rating) VALUES (:s, :n, :d, :r)"),
                           {"s": uid, "n": f"Cửa hàng {vn_cat_name} {fake.last_name()}", 
                            "d": f"Chuyên cung cấp {vn_cat_name} chính hãng toàn cầu.", 
                            "r": round(random.uniform(3.0, 5.0), 2)})
        db.commit()
        
        # TẠO VOUCHER
        print(">>> Đang sinh Vouchers cho từng Shop và Sàn...")
        vouchers_data = []
        
        # A. Voucher dành riêng cho từng Shop (1 đến 8 mã)
        for sid in seller_ids:
            num_vouchers = random.randint(1, 8)
            for _ in range(num_vouchers):
                discount_val = round(random.uniform(10.0, 55.0), 1)
                prefix = random.choice(["GIAMGIA", "SALE"])
                rounded_int = round(discount_val)
                # Đảm bảo mã unique bằng cách nối thêm ký tự ngẫu nhiên
                v_code = f"{prefix}{rounded_int}%_{fake.unique.lexify(text='????').upper()}"
                
                start_date = fake.date_time_between(start_date='-6m', end_date='now')
                vouchers_data.append({
                    "VoucherCode": v_code, "ShopID": sid, "VoucherType": "Shop", "DiscountValue": discount_val, 
                    "StartDate": start_date.strftime("%Y-%m-%d %H:%M:%S"), 
                    "EndDate": (start_date + timedelta(days=random.randint(15, 60))).strftime("%Y-%m-%d %H:%M:%S"),
                    "Status": "Active"
                })
                
        # B. Voucher của Sàn (Platform) & Vận chuyển (Shipping)
        for _ in range(150):
            discount_val = round(random.uniform(10.0, 55.0), 1)
            v_type = random.choice(['Platform', 'Shipping'])
            prefix = "FREESHIP" if v_type == 'Shipping' else random.choice(["GIAMGIA", "SALE"])
            rounded_int = round(discount_val)
            v_code = f"{prefix}{rounded_int}%_{fake.unique.lexify(text='????').upper()}"
            
            start_date = fake.date_time_between(start_date='-6m', end_date='now')
            vouchers_data.append({
                "VoucherCode": v_code, "ShopID": None, "VoucherType": v_type, "DiscountValue": discount_val, 
                "StartDate": start_date.strftime("%Y-%m-%d %H:%M:%S"), 
                "EndDate": (start_date + timedelta(days=random.randint(15, 60))).strftime("%Y-%m-%d %H:%M:%S"),
                "Status": "Active"
            })
            
        voucher_query = """
            INSERT INTO Vouchers (VoucherCode, ShopID, VoucherType, DiscountValue, StartDate, EndDate, Status) 
            VALUES (:VoucherCode, :ShopID, :VoucherType, :DiscountValue, :StartDate, :EndDate, :Status)
        """
        for i in range(0, len(vouchers_data), 500):
            db.execute(text(voucher_query), vouchers_data[i:i+500])
        db.commit()
        
        # SINH ĐỊA CHỈ
        print(">>> Đang tạo địa chỉ cho TẤT CẢ User...")
        for uid in user_ids:
            if random.random() < 0.9:
                pv = random.choice(DANH_SACH_TINH)
                dt = f"Quận {random.randint(1, 10)}"
                w = f"Phường {random.randint(1, 20)}"
                da = f"Số {random.randint(1, 999)}, {random.choice(DANH_SACH_DUONG)}"
            else:
                fa = random.choice(FOREIGN_ADDRESSES)
                pv = fa["pv"]
                dt = fa["dt"]
                w = fa["w"]
                da = fa["da"] + str(random.randint(10, 999))

            info = user_info_map[uid]
            db.execute(text("INSERT INTO Addresses (UserID, ReceiverName, Phone, Province, District, Ward, DetailAddress, IsDefault) VALUES (:u, :n, :p, :pv, :dt, :w, :da, 1)"),
                       {"u": uid, "n": info["name"], "p": info["phone"], "pv": pv, "dt": dt, "w": w, "da": da})
        db.commit()

        print(">>> Đang quét dữ liệu sản phẩm từ TẤT CẢ các file CSV...")
        all_products_pool = []
        seen_names = set()
        
        sources = {
            'amazon_reviews.csv': {'name': 'name', 'brand': 'brand', 'cat': 'Electronics', 'enc': 'utf-8', 'desc': 'name'},
            'fashion_products.csv': {'name': 'productDisplayName', 'brand': 'baseColour', 'cat': 'Fashion', 'enc': 'utf-8', 'desc': 'usage'},
            'skincare_product.csv': {'name': 'product_name', 'brand': 'brand_name', 'cat': 'Skincare', 'enc': 'utf-8', 'desc': 'ingredients'},
            'flipkart_laptops.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Laptops', 'enc': 'utf-8', 'desc': 'Details'},
            'flipkart_mobiles.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Mobiles', 'enc': 'utf-8', 'desc': 'Details'},
            'flipkart_refrigerator.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Appliances', 'enc': 'utf-8', 'desc': 'Details'},
            'flipkart_smart_watch.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Wearables', 'enc': 'utf-8', 'desc': 'Details'},
            'flipkart_tv.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Televisions', 'enc': 'utf-8', 'desc': 'Details'},
            'flipkart_washing_machine.csv': {'name': 'Name', 'brand': 'Brand', 'cat': 'Appliances', 'enc': 'utf-8', 'desc': 'Details'},
            'sports_products.csv': {'name': 'Product Name', 'brand': 'Brand', 'cat': 'Sports', 'enc': 'utf-8', 'desc': 'Description'}
        }

        for file, meta in sources.items():
            path = f'scripts/{file}'
            if os.path.exists(path):
                count_from_file = 0
                with open(path, mode='r', encoding=meta['enc'], errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        p_name = row.get(meta['name'], '').strip()
                        if p_name and p_name not in seen_names:
                            seen_names.add(p_name)
                            
                            current_cat = meta['cat']
                            # Vẫn giữ logic cũ: Nếu đồ Fashion mà có tag sport thì đổi thành Sport
                            if current_cat == 'Fashion':
                                usage_str = str(row.get('usage', '')).lower()
                                name_check = p_name.lower()
                                if 'sports' in usage_str or any(k in name_check for k in ['sport', 'run', 'gym', 'active', 'sneaker']):
                                    current_cat = 'Sports'

                            all_products_pool.append({
                                'name': p_name, 
                                'brand': row.get(meta['brand'], 'Generic'), 
                                'cat': current_cat, 
                                'desc': row.get(meta['desc'], '')
                            })
                            count_from_file += 1
                        
                        if count_from_file >= 2000: break
                print(f"  -> Đã trích xuất {count_from_file} sản phẩm từ {file}")

        if len(all_products_pool) < 6000:
            so_luong_can_them = 6000 - len(all_products_pool)
            for _ in range(so_luong_can_them):
                main_cat = random.choice(main_cats_list)
                vn_cat = MAIN_CAT_TRANSLATE[main_cat]
                fake_name = f"{vn_cat} {fake.word().capitalize()} Model {random.randint(100, 9999)}"
                all_products_pool.append({'name': fake_name, 'brand': fake.company(), 'cat': main_cat, 'desc': fake.paragraph(nb_sentences=4)})

        random.shuffle(all_products_pool)

        print(f">>> Đang lưu {len(all_products_pool)} sản phẩm và gán Cấu trúc Danh mục/Tag thông minh...")
        cat_cache = {r[1]: r[0] for r in db.execute(text("SELECT CategoryID, CategoryName FROM Categories")).fetchall()}
        tag_name_to_id = {t[1]: t[0] for t in tag_data}
        
        for item in all_products_pool:
            main_cat = item['cat']
            matching_sellers = [sid for sid, scat in shop_specialized_map.items() if scat == main_cat]
            final_sid = random.choice(matching_sellers if matching_sellers else seller_ids)

            main_cat_vn = MAIN_CAT_TRANSLATE.get(main_cat, 'Khác')
            sub_cat_vn = smart_categorize(item['name'], main_cat)
            
            target_cat_names = [main_cat_vn, sub_cat_vn]

            brand_name = str(item['brand']).strip()
            if brand_name and brand_name.lower() not in ['generic', 'none', 'no brand', 'null', '', 'unknown', 'n/a']:
                target_cat_names.append(brand_name.upper())

            if random.random() < 0.3:
                if "Nam" in sub_cat_vn: target_cat_names.append("Sản Phẩm Nam Giới")
                elif "Nữ" in sub_cat_vn: target_cat_names.append("Sản Phẩm Nữ Giới")
                elif main_cat == 'Skincare': target_cat_names.append("Chăm Sóc Sắc Đẹp")
                elif main_cat in ['Laptops', 'Mobiles', 'Televisions']: target_cat_names.append("Công Nghệ Tiên Tiến")
                elif main_cat == 'Appliances': target_cat_names.append("Điện Máy Gia Đình")
                elif main_cat == 'Sports': target_cat_names.append("Đồ Thể Thao Cao Cấp")

            if random.random() < 0.15:
                context_pool = ["Hàng Mới Về", "Top Bán Chạy", "Hàng Chính Hãng", "Lựa Chọn Của Shop"]
                target_cat_names.append(random.choice(context_pool))
            
            target_cat_names = list(set(target_cat_names))
            
            target_cat_ids = []
            for c_name in target_cat_names:
                cid = get_or_create_category(db, cat_cache, c_name)
                target_cat_ids.append(cid)

            cleaned_csv = clean_desc_conflict(item['desc'], main_cat)
            gen_phrase = random.choice(ENRICHED_DESC.get(main_cat, ["Sản phẩm chất lượng cao."]))
            final_desc = clean_and_format_desc(cleaned_csv, gen_phrase)

            res = db.execute(text("""INSERT INTO Products (ProductName, ShopID, Brand, Description) 
                                   OUTPUT INSERTED.ProductID VALUES (:n, :s, :b, :d)"""), 
                                   {"n": str(item['name'])[:200], "s": final_sid, "b": brand_name[:100], "d": final_desc[:1000]})
            pid = res.fetchone()[0]

            for cid in target_cat_ids:
                db.execute(text("INSERT INTO Product_Categories_Map (ProductID, CategoryID) VALUES (:p, :c)"), {"p": pid, "c": cid})

            base_min, base_max = PRICE_RANGES.get(main_cat, PRICE_RANGES['Default'])
            base_price = round(random.uniform(base_min, base_max), -4)

            attr_key = main_cat if main_cat in ATTR_MAP else 'Default'
            attrs = ATTR_MAP[attr_key]
            
            chosen_combos = []
            
            if main_cat in ['Fashion', 'Sports']:
                num_colors = random.randint(1, min(2, len(attrs['colors'])))
                selected_colors = random.sample(attrs['colors'], num_colors)
                
                for clr in selected_colors:
                    for sz in attrs['sizes']:
                        chosen_combos.append((sz, clr))
            else:
                all_combos = list(itertools.product(attrs['sizes'], attrs['colors']))
                num_variants = min(random.randint(1, 3), len(all_combos))
                chosen_combos = random.sample(all_combos, num_variants)
            
            for i, (sz, cl) in enumerate(chosen_combos):
                variant_price = base_price + round(base_price * random.uniform(0.05 * i, 0.2 * i), -4)
                s_sz = sanitize_sku_part(sz)
                s_cl = sanitize_sku_part(cl)
                sku = f"SKU-{pid}-{s_sz}-{s_cl}"
                
                db.execute(text("""INSERT INTO Product_Variants (ProductID, Size, Color, Price, StockQuantity, SKU, Status)
                                   VALUES (:p, :sz, :cl, :pr, :st, :s, 'Active')"""),
                                   {"p": pid, "sz": sz, "cl": cl, "pr": variant_price, "st": random.randint(10, 500), "s": sku})
            
            final_tags = set()
            spec_keywords = SPECIFIC_TAG_MAP.get(sub_cat_vn, [])
            relevant_tag_ids = [tag_name_to_id[k] for k in spec_keywords if k in tag_name_to_id]
            
            if relevant_tag_ids:
                num_to_pick = random.choice([2, 3, 4]) 
                chosen_special = random.sample(relevant_tag_ids, min(len(relevant_tag_ids), num_to_pick))
                final_tags.update(chosen_special)

            prob_tags = {'Sale': 0.15, 'New': 0.2, 'Hot Trend': 0.1, 'Có Sẵn': 0.4, 'Chính hãng': 0.3}
            for t_name, prob in prob_tags.items():
                if random.random() < prob and t_name in tag_name_to_id:
                    final_tags.add(tag_name_to_id[t_name])

            for tid in final_tags:
                db.execute(text("INSERT INTO Product_Tag_Map (ProductID, TagID) VALUES (:p, :t)"), {"p": pid, "t": tid})

            db.execute(text("INSERT INTO Product_Images (ProductID, ImageURL, IsMain) VALUES (:p, :u, 1)"), 
                       {"p": pid, "u": f"https://picsum.photos/seed/{pid}{main_cat}/600/600"})

        db.commit()
        print(">>> HOÀN THÀNH PHASE 2!")
    except Exception as e:
        db.rollback(); raise e
    finally: db.close()

if __name__ == "__main__":
    run_phase_2()
