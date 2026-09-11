import os
import json
from typing import Dict, Any, Optional
from src.config import SELECTED_BRAND, GEMINI_MODEL
from src.preprocessing import clean_text
from src.intent_classifier import AIIntentClassifier
from src.retrieval import HistoricalRetriever
from src.escalation import EscalationEngine
from src.response_generator import ResponseGenerator


class SupportAgent:
    """
    Unified AI Customer Support Agent pipeline.
    Connects:
    Preprocessing -> AI Intent Classification -> Historical Retrieval -> Escalation Engine -> Grounded Response Generation
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.brand = SELECTED_BRAND
        self.classifier = AIIntentClassifier(api_key=self.api_key)
        self.retriever = HistoricalRetriever()
        self.escalation_engine = EscalationEngine()
        self.response_generator = ResponseGenerator(api_key=self.api_key)
        self._is_initialized = False

    def initialize(self):
        """Pre-indexes historical retriever and fits baseline models."""
        if not self._is_initialized:
            self.retriever.build_index()
            self._is_initialized = True
        return self

    def process_message(self, raw_customer_message: str) -> Dict[str, Any]:
        """
        Executes end-to-end support pipeline on an incoming customer message.
        """
        self.initialize()

        # Step 1: Preprocessing & PII Masking
        cleaned_text = clean_text(raw_customer_message, mask_pii=True)

        # Step 2: Intent Classification
        classification = self.classifier.classify(cleaned_text)

        # Step 3: Historical Retrieval
        retrieved_evidence = self.retriever.retrieve(cleaned_text, top_k=3)
        evidence_sufficiency = self.retriever.assess_evidence_sufficiency(retrieved_evidence)

        # Step 4: Escalation Decision Layer
        escalation_result = self.escalation_engine.evaluate(
            cleaned_text, classification, evidence_sufficiency
        )

        # Step 5: Grounded Response Generation & Audit Explanation
        response_package = self.response_generator.generate_response(
            cleaned_text, classification, retrieved_evidence, escalation_result
        )

        return {
            "brand": self.brand,
            "raw_input": raw_customer_message,
            "cleaned_input": cleaned_text,
            "classification": classification,
            "evidence_sufficiency": evidence_sufficiency,
            "retrieved_evidence": retrieved_evidence,
            "escalation": escalation_result,
            "generated_reply": response_package["generated_reply"],
            "explanation": response_package["explanation"]
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run SupportAgent on customer input")
    parser.add_argument("--message", type=str, help="Customer message to process")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    agent = SupportAgent().initialize()
    msg = args.message if args.message else "@AppleSupport my screen is cracked and touch isn't responding after falling on concrete!"
    output = agent.process_message(msg)

    if args.json or args.message:
        print(json.dumps(output))
    else:
        print("Agent Pipeline Output:")
        print(f"Intent: {output['classification']['intent']} (Conf: {output['classification']['confidence']})")
        print(f"Escalation Decision: {output['escalation']['decision']}")
        print(f"Escalation Reason: {output['escalation']['reason']}")
        print(f"Generated Reply: {output['generated_reply']}")
