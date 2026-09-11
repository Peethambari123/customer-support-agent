import os
import json
import re
from typing import Dict, Any, Optional
from src.config import INTENT_DEFINITIONS, GEMINI_MODEL
from baselines.tfidf_logistic import TfidfLogisticBaseline


class AIIntentClassifier:
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, api_key: Optional[str] = None, model_name: str = GEMINI_MODEL):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.valid_intents = list(INTENT_DEFINITIONS.keys())
        self.ml_fallback = TfidfLogisticBaseline()
        self._is_ml_fitted = False

    def _ensure_ml_fitted(self):
        if not self._is_ml_fitted:
            self.ml_fallback.fit()
            self._is_ml_fitted = True

    def classify_with_ml(self, text: str) -> Dict[str, Any]:
        """High-speed local ML fallback using TF-IDF + Logistic Regression."""
        self._ensure_ml_fitted()
        pred_intent = self.ml_fallback.predict([text])[0]
        proba_matrix = self.ml_fallback.predict_proba([text])[0]
        class_idx = self.ml_fallback.classes_.index(pred_intent)
        confidence = float(proba_matrix[class_idx])

        return {
            "intent": pred_intent,
            "confidence": round(min(max(confidence, 0.50), 0.99), 2),
            "reason": f"Classified by local TF-IDF model based on customer terminology with probability {confidence:.2f}",
            "source": "local_tfidf_logistic"
        }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classifies incoming customer tweet into one of the canonical intents.
        Prioritizes Gemini API with structured JSON output and falls back cleanly to ML model.
        """
        if not text or not text.strip():
            return {
                "intent": "other_general",
                "confidence": 0.50,
                "reason": "Empty or whitespace-only message.",
                "source": "heuristic_fallback"
            }

        if text in AIIntentClassifier._cache:
            return AIIntentClassifier._cache[text]

        # If no Gemini API key configured, use trained ML classifier
        if not self.api_key:
            res = self.classify_with_ml(text)
            AIIntentClassifier._cache[text] = res
            return res

        # Call Gemini API
        prompt = self._build_prompt(text)
        try:
            raw_response = self._call_gemini_api(prompt)
            parsed = self._extract_json(raw_response)
            intent = parsed.get("intent", "").strip().lower()

            if intent in self.valid_intents:
                conf = parsed.get("confidence", 0.85)
                try:
                    conf = float(conf)
                except (ValueError, TypeError):
                    conf = 0.85
                res = {
                    "intent": intent,
                    "confidence": round(min(max(conf, 0.0), 1.0), 2),
                    "reason": parsed.get("reason", "Classified by Gemini LLM based on intent criteria."),
                    "source": "gemini_llm"
                }
                AIIntentClassifier._cache[text] = res
                return res
        except Exception:
            # Silent fallback to ML model to ensure zero crashes
            pass

        res = self.classify_with_ml(text)
        AIIntentClassifier._cache[text] = res
        return res

    def _build_prompt(self, text: str) -> str:
        intent_docs = "\n".join(
            [f"- {k}: {v['description']}" for k, v in INTENT_DEFINITIONS.items()]
        )
        prompt = (
            f"You are an expert customer support intent classifier for AppleSupport.\n"
            f"Analyze the following incoming customer tweet and select EXACTLY ONE intent from this list:\n"
            f"{intent_docs}\n\n"
            f"Customer Tweet:\n\"{text}\"\n\n"
            f"Respond ONLY in valid JSON matching this exact schema:\n"
            f"{{\n"
            f'  "intent": "<exact_intent_name>",\n'
            f'  "confidence": <float between 0.0 and 1.0>,\n'
            f'  "reason": "<one sentence explaining the rationale>"\n'
            f"}}"
        )
        return prompt

    def _call_gemini_api(self, prompt: str) -> str:
        import urllib.request
        import json

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            candidate = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return candidate

    def _extract_json(self, raw_str: str) -> Dict[str, Any]:
        """Extracts JSON even if wrapped in markdown code fence."""
        raw_str = raw_str.strip()
        if raw_str.startswith("```"):
            raw_str = re.sub(r"^```(?:json)?\n?", "", raw_str)
            raw_str = re.sub(r"\n?```$", "", raw_str)
        return json.loads(raw_str)


if __name__ == "__main__":
    classifier = AIIntentClassifier()
    sample = "@AppleSupport my iPhone 7 battery is draining 50% in 30 minutes after iOS update!"
    res = classifier.classify(sample)
    print("Test Classification:")
    print(json.dumps(res, indent=2))
