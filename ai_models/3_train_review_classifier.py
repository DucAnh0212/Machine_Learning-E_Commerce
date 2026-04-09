import pandas as pd
import joblib
import sys
import os

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database_connection import engine

def train_and_export_review_classifier():
    query = """
        SELECT 
            r.ReviewID,
            ISNULL(r.Comment, '') AS Comment,
            r.Rating,
            CASE WHEN r.OrderItemID IS NOT NULL THEN 1 ELSE 0 END AS Has_Order,
            ISNULL(ip_count.IP_Frequency, 1) AS IP_Frequency,
            ISNULL(device_count.Device_Frequency, 1) AS Device_Frequency,
            r.IsFake
        FROM Reviews r
        LEFT JOIN Review_Metas rm ON r.ReviewID = rm.ReviewID
        LEFT JOIN (
            SELECT IP_Address, COUNT(*) AS IP_Frequency FROM Review_Metas GROUP BY IP_Address
        ) ip_count ON rm.IP_Address = ip_count.IP_Address
        LEFT JOIN (
            SELECT DeviceID, COUNT(*) AS Device_Frequency FROM Review_Metas GROUP BY DeviceID
        ) device_count ON rm.DeviceID = device_count.DeviceID
        WHERE r.IsFake IS NOT NULL
    """
    
    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        print("Lỗi kết nối CSDL:", e)
        return

    df['Word_Count'] = df['Comment'].apply(lambda x: len(str(x).split()))
    
    X = df[['Comment', 'Rating', 'Has_Order', 'IP_Frequency', 'Device_Frequency', 'Word_Count']]
    y = df['IsFake']
    
    text_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=3000)),
        ('svd', TruncatedSVD(n_components=100, random_state=42)) 
    ])
    
    numeric_features = ['Rating', 'Has_Order', 'IP_Frequency', 'Device_Frequency', 'Word_Count']
    numeric_pipeline = Pipeline([
        ('scaler', StandardScaler())
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('text', text_pipeline, 'Comment'),
            ('num', numeric_pipeline, numeric_features)
        ]
    )

    final_model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(class_weight='balanced', random_state=42))
    ])

    final_model.fit(X, y) 

    os.makedirs('app/ml', exist_ok=True)
    export_path = 'app/ml/review_classifier.pkl'
    joblib.dump(final_model, export_path)

if __name__ == "__main__":
    train_and_export_review_classifier()