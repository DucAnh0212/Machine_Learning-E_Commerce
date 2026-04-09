import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import joblib
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database_connection import engine

def train_and_export_pca_knn():
    # Kéo dữ liệu đã được chuẩn hóa theo Database
    query = """
        SELECT 
            p.ProductID, 
            p.ProductName, 
            ISNULL(p.Brand, '') AS Brand,
            ISNULL(p.Description, '') AS Description,
            ISNULL(c.CategoryList, '') AS Category,
            ISNULL(t.TagList, '') AS Tags,
            ISNULL(v.MinPrice, 0) AS Price
        FROM Products p 
        LEFT JOIN (
            SELECT pcm.ProductID, STRING_AGG(cat.CategoryName, ' ') AS CategoryList
            FROM Product_Categories_Map pcm
            INNER JOIN Categories cat ON pcm.CategoryID = cat.CategoryID
            GROUP BY pcm.ProductID
        ) c ON p.ProductID = c.ProductID
        LEFT JOIN (
            SELECT ptm.ProductID, STRING_AGG(tg.TagName, ' ') AS TagList
            FROM Product_Tag_Map ptm
            INNER JOIN Tags tg ON ptm.TagID = tg.TagID
            GROUP BY ptm.ProductID
        ) t ON p.ProductID = t.ProductID
        LEFT JOIN (
            SELECT ProductID, MIN(Price) AS MinPrice
            FROM Product_Variants 
            WHERE DeletedAt IS NULL
            GROUP BY ProductID
        ) v ON p.ProductID = v.ProductID
        WHERE p.DeletedAt IS NULL
    """
    
    df = pd.read_sql(query, engine)
    
    # Tiền xử lý & Phân khúc giá
    df = df.fillna('')
    bins = [0, 100000, 300000, 1000000, 5000000, float('inf')]
    labels = ['gia_rat_re', 'gia_binh_dan', 'gia_trung_binh', 'gia_cao_cap', 'gia_sang_trong']
    df['PriceNumeric'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
    df['PriceTag'] = pd.cut(df['PriceNumeric'], bins=bins, labels=labels, right=False).astype(str)
    
    # Gộp đặc trưng tự nhiên 
    df['combined_features'] = df['ProductName'] + " " + df['Tags'] + " " + df['Category'] + " " + df['PriceTag'] + " " + df['Description']
    
    # Mã hóa Text
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features']).toarray()
    
    # Nén dữ liệu với PCA 
    if tfidf_matrix.shape[1] > 50:
        pca_model = PCA()
        pca_model.fit(tfidf_matrix)
        cumulative_variance = np.cumsum(pca_model.explained_variance_ratio_)
        optimal_k = np.argmax(cumulative_variance >= 0.85) + 1
        
        pca_model = PCA(n_components=optimal_k, random_state=42)
        final_matrix = pca_model.fit_transform(tfidf_matrix)
    else:
        final_matrix = tfidf_matrix

    # Xây dựng cây tìm kiếm K-NN
    n_neighbors = min(300, len(df))
    knn_model = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine') 
    knn_model.fit(final_matrix)

    # Đóng gói và Lưu file
    os.makedirs('app/ml', exist_ok=True)
    model_data = {
        'matrix': final_matrix, 
        'knn': knn_model,
        'product_ids': df['ProductID'].tolist(),
        'categories': df['Category'].tolist() 
    }
    
    export_path = 'app/ml/knn_production.pkl'
    joblib.dump(model_data, export_path)

if __name__ == "__main__":
    train_and_export_pca_knn()