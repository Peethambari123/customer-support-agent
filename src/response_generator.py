import os
import json
import re
from typing import Dict, Any, List, Optional
from src.config import SELECTED_BRAND, GEMINI_MODEL


class ResponseGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: str = GEMINI_MODEL):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name

    def generate_response(
        self,
        customer_message: str,
        classification: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
        escalation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates grounded customer support reply grounded in retrieved historical precedent.
        Produces reply and full 'Why this response?' diagnostic rationale.
        """
        intent = classification.get("intent", "other_general")
        decision = escalation_result.get("decision", "AUTO-HANDLE")

        # Select primary historical reference
        primary_match = retrieved_evidence[0] if retrieved_evidence else None
        historical_reply = primary_match.get("historical_agent_response", "") if primary_match else ""

        # Check if Gemini API is available
        if self.api_key:
            try:
                llm_reply = self._generate_with_gemini(
                    customer_message, intent, decision, escalation_result, retrieved_evidence
                )
                if llm_reply and len(llm_reply.strip()) > 10:
                    return self._package_result(
                        reply=llm_reply,
                        source="gemini_llm_grounded",
                        classification=classification,
                        retrieved_evidence=retrieved_evidence,
                        escalation_result=escalation_result
                    )
            except Exception as e:
                # Fall back to deterministic grounded generator
                pass

        # Deterministic Grounded Generation (Fallback & Offline Mode)
        grounded_reply = self._generate_deterministic_grounded_reply(
            customer_message, intent, decision, escalation_result, primary_match
        )

        return self._package_result(
            reply=grounded_reply,
            source="historical_precedent_grounded",
            classification=classification,
            retrieved_evidence=retrieved_evidence,
            escalation_result=escalation_result
        )

    def _generate_deterministic_grounded_reply(
        self,
        customer_message: str,
        intent: str,
        decision: str,
        escalation: Dict[str, Any],
        primary_match: Optional[Dict[str, Any]]
    ) -> str:
        """Constructs safe, historically styled reply adhering to AppleSupport conventions."""
        if decision == "ESCALATE":
            reason = escalation.get("reason", "")
            if intent == "account_security_appleid":
                return (
                    "We take your account security very seriously. For your privacy and protection, "
                    "password and Apple ID verification must be handled through our secure system. "
                    "Please visit https://iforgot.apple.com to reset your credentials, or reach out to us "
                    "in a private DM so an Apple advisor can assist you securely."
                )
            elif intent == "hardware_display_audio":
                return (
                    "Having physical hardware or screen damage is never ideal, but we're here to help you "
                    "explore repair and service options. We recommend scheduling an appointment at your "
                    "nearest Apple Authorized Service Provider or Genius Bar: https://locate.apple.com. "
                    "You can also DM us your device model and country so we can assist further."
                )
            else:
                return (
                    f"We're here to help you get this resolved. Because this requires specialized review "
                    f"({reason}), let's transition to a direct message. Please DM us your current device model, "
                    f"software version, and any troubleshooting steps you've already tried: https://apple.co/DM"
                )

        # AUTO-HANDLE based on grounded intent
        if intent == "battery_power":
            return (
                "We want you to enjoy optimal battery life. Which version of iOS is currently installed on your "
                "device (Settings > General > About)? Also check Settings > Battery > Battery Health to review your "
                "Maximum Capacity, and let us know which apps show the highest background usage."
            )
        elif intent == "software_update_os":
            return (
                "We're here for you and want to help ensure your update completes smoothly. "
                "First, make sure your device has at least 5GB of free local storage and is connected to a reliable Wi-Fi network. "
                "If it remains stuck, try a forced restart. You can also update securely using Finder or iTunes on your computer."
            )
        elif intent == "connectivity_network":
            return (
                "Let's get your connection back up and running. Try toggling Airplane Mode on for 15 seconds, "
                "then turn it off. If issues persist, go to Settings > General > Reset > Reset Network Settings "
                "(note this will reset saved Wi-Fi passwords). Let us know if the issue continues."
            )
        elif intent == "app_performance_crash":
            return (
                "We know how frustrating app crashes can be. First, check the App Store to ensure the app is "
                "updated to the latest version. Next, force-close the app and restart your device. "
                "If the app continues to close unexpectedly, try deleting and reinstalling it from your purchase history."
            )
        else:
            if primary_match and len(primary_match.get("historical_agent_response", "")) > 15:
                hist_text = primary_match["historical_agent_response"]
                # Clean @mentions
                hist_clean = re.sub(r'@\w+', '', hist_text).strip()
                return f"We're here to help. {hist_clean}"
            return (
                "We're here to help you with your Apple device. Could you let us know which device model and iOS "
                "version you're currently using? You can check under Settings > General > About."
            )

    def _generate_with_gemini(
        self,
        customer_message: str,
        intent: str,
        decision: str,
        escalation: Dict[str, Any],
        retrieved: List[Dict[str, Any]]
    ) -> str:
        import urllib.request

        evidence_text = "\n".join([
            f"Precedent #{i+1} (Conv: {r['conversation_id']}):\nCustomer: {r['customer_issue']}\nAgent: {r['historical_agent_response']}"
            for i, r in enumerate(retrieved[:2])
        ])

        system_instruction = (
            "You are the official customer support agent for AppleSupport on Twitter.\n"
            "Generate an authentic, grounded response to the customer tweet.\n"
            "STRICT GUIDELINES:\n"
            "1. Ground your reply directly in the provided historical support precedents.\n"
            "2. Adopt AppleSupport's tone: empathetic, professional, requesting diagnostic details (iOS version, device model).\n"
            "3. If decision is ESCALATE, advise moving to private DM or official Apple Support appointment (locate.apple.com / iforgot.apple.com).\n"
            "4. NEVER invent unverified refund amounts, return windows, or repair timelines.\n"
            "5. Keep the reply concise (under 280 characters if possible, maximum 2 short sentences)."
        )

        prompt = (
            f"{system_instruction}\n\n"
            f"Escalation Decision: {decision}\n"
            f"Intent: {intent}\n"
            f"Escalation Reason: {escalation.get('reason', 'N/A')}\n\n"
            f"Retrieved Historical Precedents:\n{evidence_text}\n\n"
            f"Customer Tweet:\n\"{customer_message}\"\n\n"
            f"Reply:"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 150}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _package_result(
        self,
        reply: str,
        source: str,
        classification: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
        escalation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Packages reply with structured 'Why this response?' audit explanation."""
        primary_match = retrieved_evidence[0] if retrieved_evidence else None

        explanation = {
            "intent_detected": classification.get("intent"),
            "intent_confidence": classification.get("confidence"),
            "classification_source": classification.get("source"),
            "escalation_decision": escalation_result.get("decision"),
            "escalation_reason": escalation_result.get("reason"),
            "risk_factors_triggered": escalation_result.get("risk_factors", []),
            "retrieved_precedent_id": primary_match.get("conversation_id") if primary_match else None,
            "retrieval_similarity": primary_match.get("similarity_score") if primary_match else 0.0,
            "safety_policy_passed": len(escalation_result.get("risk_factors", [])) == 0,
            "generation_engine": source
        }

        return {
            "generated_reply": reply,
            "explanation": explanation,
            "retrieved_evidence": retrieved_evidence
        }


if __name__ == "__main__":
    generator = ResponseGenerator()
    test_res = generator.generate_response(
        customer_message="@AppleSupport battery dies super fast after iOS 11 update",
        classification={"intent": "battery_power", "confidence": 0.82, "source": "tfidf"},
        retrieved_evidence=[{
            "conversation_id": "conv_123",
            "customer_issue": "battery draining on ios 11",
            "historical_agent_response": "Which iOS version are you running? Check Settings > Battery.",
            "similarity_score": 0.45
        }],
        escalation_result={"decision": "AUTO-HANDLE", "reason": "Verified software issue", "risk_factors": []}
    )
    print("Generated Reply:\n", test_res["generated_reply"])
    print("\nAudit Explanation:\n", json.dumps(test_res["explanation"], indent=2))
