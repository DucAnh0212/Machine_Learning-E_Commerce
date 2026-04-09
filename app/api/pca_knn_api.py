from fastapi import APIRouter, HTTPException
import joblib
import os

router = APIRouter()

# Tải Não bộ KNN vào RAM khi Server khởi động
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'knn_production.pkl')

try:
    KNN_MODEL = joblib.load(MODEL_PATH)
except Exception as e:
    KNN_MODEL = None

@router.get("/similar/{product_id}")
async def get_similar_products(product_id: int, top_n: int = 10):
    if not KNN_MODEL:
        raise HTTPException(status_code=500, detail="Mô hình K-NN chưa sẵn sàng.")

    product_ids = KNN_MODEL['product_ids']
    categories = KNN_MODEL['categories']
    matrix = KNN_MODEL['matrix']
    knn = KNN_MODEL['knn']

    # Kiểm tra Sản phẩm có tồn tại trong AI không
    if product_id not in product_ids:
        return {"success": False, "message": "Sản phẩm chưa có trong dữ liệu AI."}

    # 1. Xác định thông tin của sản phẩm mục tiêu
    idx = product_ids.index(product_id)
    target_category = str(categories[idx])
    target_cat_words = set(target_category.lower().split())

    # 2. Tìm danh sách láng giềng thô
    n_neighbors = min(300, len(product_ids))
    distances, indices = knn.kneighbors([matrix[idx]], n_neighbors=n_neighbors)

    recs = []
    
    # 3. Quét qua Bộ lọc mềm (Soft Filter)
    for i in range(1, len(indices[0])): 
        neighbor_idx = indices[0][i]
        neighbor_id = product_ids[neighbor_idx]
        neighbor_category = str(categories[neighbor_idx])
        
        neighbor_cat_words = set(neighbor_category.lower().split())

        if not target_cat_words or not neighbor_cat_words:
            is_valid = True
        else:
            overlap = len(target_cat_words.intersection(neighbor_cat_words))
            min_len = min(len(target_cat_words), len(neighbor_cat_words))
            is_valid = (overlap / min_len) >= 0.4 if min_len > 0 else True
            
        if is_valid:
            sim_score = round((1 - distances[0][i]) * 100, 1)
            recs.append({
                "product_id": neighbor_id, 
                "ai_score": sim_score
            })
            
            if len(recs) >= top_n:
                break

    return {
        "success": True, 
        "product_id": product_id, 
        "data": recs
    }