import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from sklearn.preprocessing import LabelEncoder

class SalesFeatureExtractor:
    def __init__(self):
        self.product_encoder = LabelEncoder()
        self.region_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        self.feature_names = []
        self.is_fitted = False

    def _extract_datetime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        dt_series = pd.to_datetime(df["date"], errors="coerce").fillna(pd.Timestamp.now())
        df["month"] = dt_series.dt.month
        df["day"] = dt_series.dt.day
        df["year"] = dt_series.dt.year
        df["quarter"] = dt_series.dt.quarter
        df["day_of_week"] = dt_series.dt.dayofweek
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        return df

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        df = self._extract_datetime_features(df)
        
        # Fit label encoders
        df["product_enc"] = self.product_encoder.fit_transform(df["product"].astype(str))
        df["region_enc"] = self.region_encoder.fit_transform(df["region"].astype(str))
        if "category" in df.columns:
            df["category_enc"] = self.category_encoder.fit_transform(df["category"].astype(str))
        else:
            df["category_enc"] = 0

        self.feature_names = [
            "quantity", "price", "product_enc", "region_enc", 
            "category_enc", "month", "day", "year", "quarter", "day_of_week", "is_weekend"
        ]

        X = df[self.feature_names].values
        y = df["revenue"].values
        self.is_fitted = True
        return X, y

    def transform_single(self, product: str, region: str, quantity: int, price: float, target_date: str) -> np.ndarray:
        dt = pd.to_datetime(target_date, errors="coerce")
        if pd.isna(dt):
            dt = pd.Timestamp.now()

        month = dt.month
        day = dt.day
        year = dt.year
        quarter = dt.quarter
        day_of_week = dt.dayofweek
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Encode categorical safely
        try:
            prod_enc = self.product_encoder.transform([str(product)])[0]
        except Exception:
            prod_enc = 0

        try:
            reg_enc = self.region_encoder.transform([str(region)])[0]
        except Exception:
            reg_enc = 0

        category_enc = 0 # Default

        features = np.array([[
            quantity, price, prod_enc, reg_enc, 
            category_enc, month, day, year, quarter, day_of_week, is_weekend
        ]])
        return features
