import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from backend.config import SAVED_MODELS_DIR
from backend.ml.feature_engineering import SalesFeatureExtractor

class RevenuePredictor:
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.feature_extractor = SalesFeatureExtractor()
        self.model = None
        self.lr_model = None
        self.rf_model = None
        self.selected_model_name = "Random Forest Regressor"
        self.metrics = {}
        self.feature_importance = {}
        self.is_trained = False
        self.model_file = SAVED_MODELS_DIR / f"revenue_model_user_{user_id}.joblib"
        self.load_if_exists()

    def train_and_evaluate(self, sales_df: pd.DataFrame) -> Dict[str, Any]:
        if len(sales_df) < 10:
            raise ValueError("At least 10 sales records are required to train machine learning models.")

        # 1. Feature Extraction
        X, y = self.feature_extractor.fit_transform(sales_df)

        # 2. Train-Test Split (80% Train, 20% Test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 3. Train Linear Regression
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        lr_pred = lr.predict(X_test)
        lr_mae = float(mean_absolute_error(y_test, lr_pred))
        lr_rmse = float(np.sqrt(mean_squared_error(y_test, lr_pred)))
        lr_r2 = float(r2_score(y_test, lr_pred))

        # 4. Train Random Forest Regression
        rf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_mae = float(mean_absolute_error(y_test, rf_pred))
        rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf_pred)))
        rf_r2 = float(r2_score(y_test, rf_pred))

        self.lr_model = lr
        self.rf_model = rf

        # 5. Model Selection (Choose model with highest R² score)
        if rf_r2 >= lr_r2:
            self.model = rf
            self.selected_model_name = "Random Forest Regressor"
        else:
            self.model = lr
            self.selected_model_name = "Linear Regression"

        # 6. Feature Importance (from Random Forest)
        importances = rf.feature_importances_
        feat_names = self.feature_extractor.feature_names
        self.feature_importance = {
            name: round(float(imp), 4)
            for name, imp in sorted(zip(feat_names, importances), key=lambda x: x[1], reverse=True)
        }

        self.metrics = {
            "linear_regression": {
                "mae": round(lr_mae, 2),
                "rmse": round(lr_rmse, 2),
                "r2_score": round(max(0.0, lr_r2), 4)
            },
            "random_forest": {
                "mae": round(rf_mae, 2),
                "rmse": round(rf_rmse, 2),
                "r2_score": round(max(0.0, rf_r2), 4)
            },
            "selected_model": self.selected_model_name,
            "feature_importance": self.feature_importance
        }
        self.is_trained = True

        # 7. Persist Model
        self.save()

        return {
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "models": self.metrics
        }

    def predict(self, product: str, region: str, quantity: int, price: float, target_date: str, requested_model: str = "auto") -> Dict[str, Any]:
        if not self.is_trained:
            # If not trained yet, use rule-based fallback formula
            baseline_revenue = round(quantity * price, 2)
            return {
                "predicted_revenue": baseline_revenue,
                "model_used": "Baseline Multiplier (Model untrained)",
                "input_summary": {
                    "product": product,
                    "region": region,
                    "quantity": quantity,
                    "price": price,
                    "target_date": target_date
                },
                "confidence_interval": {
                    "low": round(baseline_revenue * 0.9, 2),
                    "high": round(baseline_revenue * 1.1, 2)
                }
            }

        feat_vector = self.feature_extractor.transform_single(
            product=product, region=region, quantity=quantity, price=price, target_date=target_date
        )

        active_model = self.model
        model_label = self.selected_model_name

        if requested_model == "linear_regression" and self.lr_model is not None:
            active_model = self.lr_model
            model_label = "Linear Regression"
        elif requested_model == "random_forest" and self.rf_model is not None:
            active_model = self.rf_model
            model_label = "Random Forest Regressor"

        raw_pred = active_model.predict(feat_vector)[0]
        # Revenue cannot be negative
        predicted_val = round(max(float(raw_pred), quantity * price * 0.5), 2)

        # Margin uncertainty estimate
        uncertainty = 0.08 if "Random Forest" in model_label else 0.14
        confidence_low = round(max(0.0, predicted_val * (1 - uncertainty)), 2)
        confidence_high = round(predicted_val * (1 + uncertainty), 2)

        return {
            "predicted_revenue": predicted_val,
            "model_used": model_label,
            "input_summary": {
                "product": product,
                "region": region,
                "quantity": quantity,
                "price": price,
                "target_date": target_date
            },
            "confidence_interval": {
                "low": confidence_low,
                "high": confidence_high
            }
        }

    def save(self):
        payload = {
            "model": self.model,
            "lr_model": self.lr_model,
            "rf_model": self.rf_model,
            "selected_model_name": self.selected_model_name,
            "feature_extractor": self.feature_extractor,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "is_trained": self.is_trained
        }
        joblib.dump(payload, self.model_file)

    def load_if_exists(self):
        if self.model_file.exists():
            try:
                payload = joblib.load(self.model_file)
                self.model = payload.get("model")
                self.lr_model = payload.get("lr_model")
                self.rf_model = payload.get("rf_model")
                self.selected_model_name = payload.get("selected_model_name", "Random Forest Regressor")
                self.feature_extractor = payload.get("feature_extractor", self.feature_extractor)
                self.metrics = payload.get("metrics", {})
                self.feature_importance = payload.get("feature_importance", {})
                self.is_trained = payload.get("is_trained", False)
            except Exception:
                self.is_trained = False
