from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.svd_api import router as svd_router
from app.api.pca_knn_api import router as pca_knn_router
from app.api.review_classifier_api import router as review_router

app = FastAPI(title="TTCS E-commerce AI API", version="1.0")

# Cấu hình CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(svd_router, prefix="/api/ai/svd", tags=["SVD Recommendation"])
app.include_router(pca_knn_router, prefix="/api/ai/pca-knn", tags=["PCA + KNN Similar Products"])
app.include_router(review_router, prefix="/api/ai/reviews", tags=["Review Fake/Spam Classifier"])

@app.get("/")
def root():
    return {"message": "Thành công"}