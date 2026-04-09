import pandas as pd
import os

# Đường dẫn đến thư mục chứa các file csv
folder_path = 'scripts'

# Danh sách các file cần kiểm tra
csv_files = [
    'amazon_reviews.csv',
    'fashion_products.csv',
    'skincare_product.csv',
    'flipkart_laptops.csv',
    'flipkart_mobiles.csv',
    'flipkart_refrigerator.csv',
    'flipkart_smart_watch.csv',
    'flipkart_tv.csv',
    'flipkart_washing_machine.csv', 
    'sports_products.csv'
]

def check_datasets():
    print(f"{'FILE NAME':<30} | {'COLUMNS FOUND'}")
    print("-" * 80)
    
    for file in csv_files:
        path = os.path.join(folder_path, file)
        if os.path.exists(path):
            try:
                # Thử đọc với utf-8, nếu lỗi thì chuyển sang latin-1 cho các file Flipkart
                encoding = 'utf-8'
                if 'flipkart' in file:
                    encoding = 'latin-1'
                
                # Chỉ đọc 5 dòng để lấy header và sample cho nhanh
                df = pd.read_csv(path, nrows=5, encoding=encoding)
                
                print(f"{file:<30} | {', '.join(df.columns.tolist())}")
                print(f"--- Sample Data (Dòng 1): {df.iloc[0].to_dict()}\n")
                
            except Exception as e:
                print(f"Lỗi khi đọc {file}: {e}")
        else:
            print(f"⚠️ Không tìm thấy file: {file}")

if __name__ == "__main__":
    check_datasets()