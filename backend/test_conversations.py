import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.db import init_db, SessionLocal
from backend.database.models import User, Sale, ChatHistory
from backend.services.auth_service import hash_password
from backend.services.data_processing import generate_sample_sales_data, save_dataframe_to_db
from backend.ml.predictor import RevenuePredictor
from backend.ai_agent.agent import AISalesAnalystAgent

class TestConversationalAnalyst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()
        
        # Create test user
        cls.user = cls.db.query(User).filter(User.username == "test_conversation_user").first()
        if not cls.user:
            cls.user = User(
                username="test_conversation_user",
                email="test_conv@example.com",
                password_hash=hash_password("Pass12345!")
            )
            cls.db.add(cls.user)
            cls.db.commit()
            cls.db.refresh(cls.user)

        # Clear existing test sales & history for clean run
        cls.db.query(Sale).filter(Sale.user_id == cls.user.id).delete()
        cls.db.query(ChatHistory).filter(ChatHistory.user_id == cls.user.id).delete()
        cls.db.commit()

        # Seed sample sales dataset
        df = generate_sample_sales_data(num_records=500)
        save_dataframe_to_db(df, cls.user.id, cls.db)

        # Train ML model
        predictor = RevenuePredictor(user_id=cls.user.id)
        predictor.train_and_evaluate(df)

        cls.agent = AISalesAnalystAgent(user_id=cls.user.id, db=cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _record_turn(self, user_msg: str, ai_msg: str):
        u_log = ChatHistory(user_id=self.user.id, role="user", message=user_msg)
        a_log = ChatHistory(user_id=self.user.id, role="assistant", message=ai_msg)
        self.db.add(u_log)
        self.db.add(a_log)
        self.db.commit()

    def test_01_greeting(self):
        res = self.agent.chat("Hey")
        self.assertEqual(len(res["tool_calls"]), 0, "Greetings must NOT invoke sales tools.")
        self.assertTrue(any(w in res["reply"].lower() for w in ["hello", "hey", "hi", "help"]))
        self._record_turn("Hey", res["reply"])

    def test_02_capabilities(self):
        res = self.agent.chat("What can you do?")
        self.assertEqual(len(res["tool_calls"]), 0, "Capabilities question must NOT invoke sales tools.")
        self.assertTrue(len(res["reply"]) > 40)
        self.assertTrue("sales" in res["reply"].lower() or "revenue" in res["reply"].lower())
        self._record_turn("What can you do?", res["reply"])

    def test_03_which_product_best(self):
        res = self.agent.chat("Which product is performing best?")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "product_analysis_tool")
        self.assertTrue("$" in res["reply"])
        self.assertTrue("revenue" in res["reply"].lower() or "best" in res["reply"].lower())
        self._record_turn("Which product is performing best?", res["reply"])

    def test_04_why_followup(self):
        # Must understand previous context about best product
        res = self.agent.chat("Why?")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "product_analysis_tool")
        self.assertTrue("price" in res["reply"].lower() or "volume" in res["reply"].lower() or "units" in res["reply"].lower() or "$" in res["reply"])
        self._record_turn("Why?", res["reply"])

    def test_05_how_are_regions_performing(self):
        res = self.agent.chat("How are the regions performing?")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "regional_breakdown_tool")
        self.assertTrue("North" in res["reply"] or "South" in res["reply"] or "East" in res["reply"] or "West" in res["reply"])
        self.assertTrue("$" in res["reply"])
        self._record_turn("How are the regions performing?", res["reply"])

    def test_06_compare_south_and_west(self):
        res = self.agent.chat("Compare South and West.")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "comparison_tool")
        self.assertTrue("South" in res["reply"])
        self.assertTrue("West" in res["reply"])
        self.assertTrue("$" in res["reply"])
        self._record_turn("Compare South and West.", res["reply"])

    def test_07_why_did_revenue_decrease(self):
        res = self.agent.chat("Why did revenue decrease?")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "trend_analysis_tool")
        self.assertTrue("revenue" in res["reply"].lower() or "drop" in res["reply"].lower() or "decrease" in res["reply"].lower() or "month" in res["reply"].lower())
        self._record_turn("Why did revenue decrease?", res["reply"])

    def test_08_what_should_i_do_next_month(self):
        res = self.agent.chat("What should I do next month?")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertTrue("1." in res["reply"] or "recommend" in res["reply"].lower() or "product" in res["reply"].lower())
        self._record_turn("What should I do next month?", res["reply"])

    def test_09_predict_next_months_revenue(self):
        res = self.agent.chat("Predict next month's revenue.")
        self.assertGreaterEqual(len(res["tool_calls"]), 1)
        self.assertEqual(res["tool_calls"][0]["tool_name"], "prediction_tool")
        self.assertTrue("$" in res["reply"])
        self.assertTrue("model" in res["reply"].lower() or "confidence" in res["reply"].lower() or "forecast" in res["reply"].lower())
        self._record_turn("Predict next month's revenue.", res["reply"])

    def test_10_thanks(self):
        res = self.agent.chat("Thanks")
        self.assertEqual(len(res["tool_calls"]), 0, "Thanks must NOT invoke sales tools.")
        self.assertTrue("welcome" in res["reply"].lower() or "help" in res["reply"].lower())
        self._record_turn("Thanks", res["reply"])

if __name__ == "__main__":
    unittest.main()
