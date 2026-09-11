import re
from typing import Dict, Any, List
from src.config import CONFIDENCE_THRESHOLD, SIMILARITY_THRESHOLD

# High-severity safety or legal keywords requiring immediate escalation
CRITICAL_SAFETY_KEYWORDS = [
    r'\bswollen\b', r'\bsmoke\b', r'\bfire\b', r'\bspark(?:ing|s)?\b',
    r'\bburn(?:ed|ing)?\b', r'\bexplod(?:ed|ing)?\b', r'\belectric\s+shock\b'
]

EXPLICIT_HUMAN_KEYWORDS = [
    r'\bspeak\s+to\s+(?:a\s+)?human\b', r'\breal\s+person\b', r'\bhuman\s+agent\b',
    r'\btalk\s+to\s+someone\b', r'\bsupervisor\b', r'\bmanager\b', r'\blawyer\b',
    r'\blawsuit\b', r'\bpolice\b', r'\bfraud\b', r'\bstolen\b'
]

HIGH_RISK_INTENTS = {"account_security_appleid", "hardware_display_audio"}


class EscalationEngine:
    def __init__(
        self,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        similarity_threshold: float = SIMILARITY_THRESHOLD
    ):
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

    def evaluate(
        self,
        customer_message: str,
        classification: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Explicit escalation decision layer.
        Returns {"decision": "ESCALATE" | "AUTO-HANDLE", "reason": "...", "risk_factors": [...]}.
        """
        text_lower = customer_message.lower()
        risk_factors: List[str] = []
        escalation_reasons: List[str] = []

        # 1. Thermal & physical safety risk (Highest priority)
        for pat in CRITICAL_SAFETY_KEYWORDS:
            if re.search(pat, text_lower):
                risk_factors.append("CRITICAL_THERMAL_SAFETY_HAZARD")
                escalation_reasons.append("Safety hazard detected: battery or hardware thermal issue requires urgent safety protocol.")
                break

        # 2. Explicit human advisor / legal / fraud trigger
        for pat in EXPLICIT_HUMAN_KEYWORDS:
            if re.search(pat, text_lower):
                risk_factors.append("EXPLICIT_HUMAN_OR_LEGAL_ESCALATION")
                escalation_reasons.append("Customer explicitly requested a human specialist or signaled legal/fraud concern.")
                break

        # 3. High-risk intent policy
        intent = classification.get("intent", "other_general")
        if intent == "account_security_appleid":
            risk_factors.append("HIGH_RISK_INTENT_ACCOUNT_SECURITY")
            escalation_reasons.append("Account security, 2FA, or payment credentials require human advisor identity verification.")
        elif intent == "hardware_display_audio":
            risk_factors.append("HIGH_RISK_INTENT_HARDWARE_DAMAGE")
            escalation_reasons.append("Physical hardware damage or component repair requires Genius Bar / service provider appointment.")

        # 4. Low classifier confidence
        clf_conf = classification.get("confidence", 0.0)
        if clf_conf < self.confidence_threshold:
            risk_factors.append("LOW_CLASSIFICATION_CONFIDENCE")
            escalation_reasons.append(
                f"Classifier confidence ({clf_conf:.2f}) is below automated routing threshold ({self.confidence_threshold:.2f})."
            )

        # 5. Low retrieval grounding / insufficient historical precedent
        sim_score = evidence.get("max_similarity", 0.0)
        if not evidence.get("sufficient", False) or sim_score < self.similarity_threshold:
            risk_factors.append("INSUFFICIENT_HISTORICAL_EVIDENCE")
            escalation_reasons.append(
                f"Historical retrieval similarity ({sim_score:.2f}) is below grounded support threshold ({self.similarity_threshold:.2f})."
            )

        # Decision synthesis
        if risk_factors:
            primary_reason = escalation_reasons[0]
            return {
                "decision": "ESCALATE",
                "reason": primary_reason,
                "all_reasons": escalation_reasons,
                "risk_factors": risk_factors,
                "confidence_score": clf_conf,
                "similarity_score": sim_score
            }

        return {
            "decision": "AUTO-HANDLE",
            "reason": "Intent identified with high confidence and verified against historical troubleshooting precedent.",
            "all_reasons": [],
            "risk_factors": [],
            "confidence_score": clf_conf,
            "similarity_score": sim_score
        }


if __name__ == "__main__":
    engine = EscalationEngine()
    test_res = engine.evaluate(
        "@AppleSupport my screen is cracked and I need an advisor",
        {"intent": "hardware_display_audio", "confidence": 0.88},
        {"sufficient": True, "max_similarity": 0.35}
    )
    print("Escalation Decision:")
    print(test_res)
