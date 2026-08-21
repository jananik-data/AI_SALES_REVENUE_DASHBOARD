import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.db import init_db, SessionLocal
from backend.database.models import User, Sale
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.services.data_processing import generate_sample_sales_data, save_dataframe_to_db
from backend.ml.predictor import RevenuePredictor
from backend.ai_agent.agent import AISalesAnalystAgent
from backend.services.report_service import generate_executive_report_json, generate_html_report

class TestSalesRevenueBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()
        
        # Create test user
        cls.user = cls.db.query(User).filter(User.username == "test_unit_user").first()
        if not cls.user:
            cls.user = User(
                username="test_unit_user",
                email="test_unit@example.com",
                password_hash=hash_password("UnitPass123!")
            )
            cls.db.add(cls.user)
            cls.db.commit()
            cls.db.refresh(cls.user)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_password_hashing(self):
        pw = "MySecret123!"
        hashed = hash_password(pw)
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_02_sample_data_generation_and_storage(self):
        df = generate_sample_sales_data(num_records=100)
        self.assertEqual(len(df), 100)
        self.assertTrue("revenue" in df.columns)
        self.assertTrue("quantity" in df.columns)
        self.assertTrue("price" in df.columns)

        inserted = save_dataframe_to_db(df, self.user.id, self.db)
        self.assertEqual(inserted, 100)

        count = self.db.query(Sale).filter(Sale.user_id == self.user.id).count()
        self.assertGreaterEqual(count, 100)

    def test_03_ml_training_and_prediction(self):
        predictor = RevenuePredictor(user_id=self.user.id)
        df = generate_sample_sales_data(num_records=120)
        res = predictor.train_and_evaluate(df)
        
        self.assertTrue(predictor.is_trained)
        self.assertIn("linear_regression", res["models"])
        self.assertIn("random_forest", res["models"])
        self.assertIn("selected_model", res["models"])

        pred = predictor.predict(
            product="Smart 4K Ultra OLED TV",
            region="North",
            quantity=5,
            price=899.99,
            target_date="2026-09-15"
        )
        self.assertGreater(pred["predicted_revenue"], 0)
        self.assertIn("confidence_interval", pred)

    def test_04_ai_agent_reasoning(self):
        agent = AISalesAnalystAgent(user_id=self.user.id, db=self.db)
        chat_res = agent.chat("What are our best selling products and how is the North region doing?")
        self.assertTrue(len(chat_res["reply"]) > 50)
        self.assertGreaterEqual(len(chat_res["tool_calls"]), 1)

        insights_res = agent.generate_automated_insights()
        self.assertGreaterEqual(len(insights_res["insights"]), 1)
        self.assertGreaterEqual(len(insights_res["recommendations"]), 1)

    def test_05_report_generation(self):
        report_json = generate_executive_report_json(self.db, self.user_id) if hasattr(self, 'user_id') else generate_executive_report_json(self.db, self.user.id)
        self.assertIn("kpis", report_json)
        self.assertIn("top_products", report_json)

        html = generate_html_report(self.db, self.user.id)
        self.assertTrue("<!DOCTYPE html>" in html)
        self.assertTrue("Executive Intelligence Report" in html)

if __name__ == "__main__":
    unittest.main()
