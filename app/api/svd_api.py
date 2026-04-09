from fastapi import APIRouter, HTTPException
import joblib
import numpy as np
import os
import requests

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'svd_production.pkl')

try:
    SVD_MODEL = joblib.load(MODEL_PATH)
except Exception as e:
    SVD_MODEL = None

# Endpoint để reload mô hình từ file (dùng sau khi chạy lại script huấn luyện)
@router.post("/reload-model")
async def reload_ai_model():
    global SVD_MODEL 
    try:
        SVD_MODEL = joblib.load(MODEL_PATH)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi nạp file: {str(e)}")

@router.get("/recommend/{user_id}")
async def recommend_products(user_id: int, top_n: int = 10):
    if not SVD_MODEL:
        raise HTTPException(status_code=500, detail="Mô hình chưa sẵn sàng.")

    # Logic xử lý khách hàng mới (cold start cho mô hình SVD)
    if user_id not in SVD_MODEL['user_ids']:
        return {
            "success": True, 
            "user_id": user_id, 
            "data": SVD_MODEL['top_popular_fallback'][:top_n]
        }

    # Logic xử lý khách hàng cũ
    user_idx = SVD_MODEL['user_ids'].index(user_id)
    user_vector = SVD_MODEL['user_factors'][user_idx]
    
    # Nhân ma trận
    predicted_normalized = np.dot(user_vector, SVD_MODEL['item_factors'])
    predicted_ratings = predicted_normalized + SVD_MODEL['user_means'][user_id]
    
    # Lọc đồ đã mua
    history = SVD_MODEL['user_history'].get(user_id, set())
    sorted_indices = np.argsort(predicted_ratings)[::-1]
    
    recs = []
    for idx in sorted_indices:
        pid = SVD_MODEL['product_ids'][idx]
        if pid not in history:
            recs.append({"product_id": pid, "ai_score": round(predicted_ratings[idx], 2)})
        if len(recs) >= top_n: break
        
    return {
        "success": True, 
        "user_id": user_id, 
        "data": recs
    }