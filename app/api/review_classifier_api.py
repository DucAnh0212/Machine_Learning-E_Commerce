from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'review_production.pkl')

try:
    REVIEW_MODEL = joblib.load(MODEL_PATH)
except Exception as e:
    REVIEW_MODEL = None

# ĐỊNH NGHĨA ĐẦU VÀO (Backend gửi lên)
class ReviewPayload(BaseModel):
    review_id: int      # ID review để backend dễ map lại
    comment: str
    rating: int
    has_order: int      # 1 nếu có OrderItemID, 0 nếu không
    ip_frequency: int   # Backend đếm số lần IP này xuất hiện trong db gửi lên
    device_frequency: int # Backend đếm số lần DeviceID này xuất hiện

@router.post("/moderate-review")
async def moderate_review(payload: ReviewPayload):
    if not REVIEW_MODEL:
        raise HTTPException(status_code=500, detail="Mô hình kiểm duyệt Review chưa sẵn sàng.")

    # 1. Tính toán Word_Count
    word_count = len(str(payload.comment).split())

    # 2. Định dạng lại thành DataFrame 1 dòng chuẩn theo quy trình Train
    input_df = pd.DataFrame([{
        'Comment': payload.comment,
        'Rating': payload.rating,
        'Has_Order': payload.has_order,
        'IP_Frequency': payload.ip_frequency,
        'Device_Frequency': payload.device_frequency,
        'Word_Count': word_count
    }])

    # 3. Kêu gọi AI dự đoán
    probabilities = REVIEW_MODEL.predict_proba(input_df)[0]
    fake_probability = probabilities[1] 

    is_fake = bool(fake_probability >= 0.60)
    
    # ĐỊNH NGHĨA ĐẦU RA 
    return {
        "success": True,
        "review_id": payload.review_id,
        "is_fake": is_fake,
        "fake_probability": round(float(fake_probability) * 100, 2),
        "action": "hide" if is_fake else "publish"
    }