import pandas as pd
from sklearn.decomposition import TruncatedSVD
import joblib
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database_connection import engine

def train_and_export_svd():
    query = "SELECT UserID, ProductID, Rating FROM Reviews WHERE IsFake = 0"
    df = pd.read_sql(query, engine)

    pivot_df = df.pivot_table(index='UserID', columns='ProductID', values='Rating', aggfunc='mean')
    
    # Tính điểm trung bình của mỗi User và chuẩn hóa ma trận
    user_ratings_mean = pivot_df.mean(axis=1)
    normalized_matrix = pivot_df.sub(user_ratings_mean, axis=0).fillna(0)
    
    n_components = min(50, normalized_matrix.shape[1] - 1) 
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    
    user_factors = svd.fit_transform(normalized_matrix)
    item_factors = svd.components_

    popular_products = df.groupby('ProductID').size().sort_values(ascending=False).head(20).index.tolist()
    
    # Ghi nhớ lịch sử mua hàng của từng User để không gợi ý lại chính sản phẩm đã mua
    user_history = df.groupby('UserID')['ProductID'].apply(set).to_dict()

    os.makedirs('app/ml', exist_ok=True)
    
    # Đóng gói mô hình
    model_data = {
        'user_factors': user_factors,
        'item_factors': item_factors,
        'user_ids': pivot_df.index.tolist(),
        'product_ids': pivot_df.columns.tolist(),
        'user_means': user_ratings_mean.to_dict(), #
        'top_popular_fallback': popular_products,  
        'user_history': user_history               
    }
    
    export_path = 'app/ml/svd_production.pkl'
    joblib.dump(model_data, export_path)
    
    try:
        res = requests.post("http://localhost:8000/api/ai/reload-model")
        if res.status_code == 200:
            print("Đã gọi API reload-model thành công sau khi huấn luyện xong")
        else:
            print("Web Server báo lỗi:", res.text)
    except Exception as e:
        print("Không gọi được Web Server.")

if __name__ == "__main__":  
    train_and_export_svd()