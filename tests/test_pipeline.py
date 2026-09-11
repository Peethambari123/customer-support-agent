import unittest
from src.preprocessing import clean_text, is_valid_message
from src.intent_classifier import AIIntentClassifier
from src.retrieval import HistoricalRetriever
from src.escalation import EscalationEngine
from src.response_generator import ResponseGenerator
from src.agent import SupportAgent
from src.config import INTENT_DEFINITIONS


class TestSupportPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = SupportAgent().initialize()
        cls.retriever = HistoricalRetriever().build_index()
        cls.classifier = AIIntentClassifier()
        cls.escalation = EscalationEngine()
        cls.generator = ResponseGenerator()

    def test_pii_masking(self):
        raw = "My email is john.appleseed@example.com and phone is 408-555-0199 for order #49281729."
        cleaned = clean_text(raw, mask_pii=True)
        self.assertNotIn("john.appleseed@example.com", cleaned)
        self.assertIn("[EMAIL]", cleaned)
        self.assertNotIn("408-555-0199", cleaned)
        self.assertIn("[PHONE]", cleaned)

    def test_intent_classification_taxonomy(self):
        text = "@AppleSupport my iPhone 8 battery drains from 100% to 20% in 1 hour."
        res = self.classifier.classify(text)
        self.assertIn("intent", res)
        self.assertIn(res["intent"], INTENT_DEFINITIONS)
        self.assertTrue(0.0 <= res["confidence"] <= 1.0)
        self.assertEqual(res["intent"], "battery_power")

    def test_historical_retrieval(self):
        query = "screen cracked after dropping iPhone"
        results = self.retriever.retrieve(query, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertIn("similarity_score", results[0])
        self.assertIn("historical_agent_response", results[0])
        self.assertGreater(results[0]["similarity_score"], 0.0)

    def test_escalation_safety_hardware_damage(self):
        damage_query = "My battery is swollen and screen is lifting, smells like smoke!"
        clf_res = {"intent": "hardware_damage", "confidence": 0.95}
        ev_res = {"sufficient": False, "max_similarity": 0.1}
        decision = self.escalation.evaluate(damage_query, clf_res, ev_res)
        self.assertEqual(decision["decision"], "ESCALATE")
        self.assertIn("CRITICAL_THERMAL_SAFETY_HAZARD", decision["risk_factors"])

    def test_escalation_low_confidence(self):
        ambiguous_query = "idk what happened just strange stuff"
        clf_res = {"intent": "other_general", "confidence": 0.40}
        ev_res = {"sufficient": False, "max_similarity": 0.12}
        decision = self.escalation.evaluate(ambiguous_query, clf_res, ev_res)
        self.assertEqual(decision["decision"], "ESCALATE")
        self.assertIn("LOW_CLASSIFICATION_CONFIDENCE", decision["risk_factors"])

    def test_grounded_response_generation(self):
        query = "@AppleSupport my bluetooth won't connect to my car stereo."
        clf = {"intent": "connectivity_network", "confidence": 0.88}
        evidence = self.retriever.retrieve(query, top_k=2)
        esc = {"decision": "AUTO-HANDLE", "risk_factors": [], "reason": "Standard guided settings self-service."}
        res_pkg = self.generator.generate_response(query, clf, evidence, esc)
        reply = res_pkg["generated_reply"]
        self.assertTrue(len(reply) > 20)
        # Verify agent never asks customer to share confidential credentials
        self.assertNotIn("send your password", reply.lower())
        self.assertNotIn("credit card", reply.lower())

    def test_end_to_end_agent(self):
        raw = "@AppleSupport my iOS 11 update is stuck on preparing update for 4 hours! Help!"
        result = self.agent.process_message(raw)
        self.assertEqual(result["brand"], "AppleSupport")
        self.assertIn("classification", result)
        self.assertIn("retrieved_evidence", result)
        self.assertIn("escalation", result)
        self.assertIn("generated_reply", result)
        self.assertIn("explanation", result)
        self.assertIn("retrieval_similarity", result["explanation"])


if __name__ == "__main__":
    unittest.main()
