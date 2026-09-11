import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from src.config import TRAIN_DATA_PATH, INTENTS_CONFIG_PATH, INTENT_DEFINITIONS

# High-precision heuristic keyword patterns derived from customer issues in the dataset
INTENT_KEYWORD_PATTERNS = {
    "battery_power": [
        r'\bbattery\b', r'\bdrain\b', r'\bcharg(?:ing|er|ed)?\b', r'\boverheat(?:ing|ed)?\b',
        r'\bdying\b', r'\bpower(?:ing)?\s+off\b', r'\bshut(?:ting)?\s+down\b', r'\bpercentage\b'
    ],
    "software_update_os": [
        r'\bios\b', r'\bupdate\b', r'\bupdating\b', r'\bupdated\b', r'\binstall(?:ing|ed)?\b',
        r'\bversion\b', r'\b11\.\d\b', r'\bapple\s+logo\b', r'\brestore\b', r'\bitunes\b'
    ],
    "account_security_appleid": [
        r'\bapple\s*id\b', r'\bicloud\b', r'\bpassword\b', r'\blocked\b', r'\bhacked\b',
        r'\bverification\b', r'\btwo[- ]factor\b', r'\bsecurity\s+reasons\b', r'\bunauthorized\b',
        r'\bbilling\b', r'\bpurchase\b', r'\bcharged\b', r'\brefund\b'
    ],
    "hardware_display_audio": [
        r'\bscreen\b', r'\bcrack(?:ed)?\b', r'\bdisplay\b', r'\btouch\b', r'\bspeaker\b',
        r'\bmicrophone\b', r'\bmic\b', r'\bsound\b', r'\bvolume\b', r'\bcamera\b',
        r'\bglass\b', r'\bbroken\b', r'\bhardware\b', r'\bheadphone\b', r'\bjack\b'
    ],
    "connectivity_network": [
        r'\bwi[- ]?fi\b', r'\bbluetooth\b', r'\bairpods\b', r'\bconnect(?:ing|ion|ed)?\b',
        r'\bcellular\b', r'\bno\s+service\b', r'\bsim\b', r'\bdata\b', r'\bhotspot\b',
        r'\bsignal\b', r'\bcarrier\b'
    ],
    "app_performance_crash": [
        r'\bapp\b', r'\bapps\b', r'\bcrash(?:ing|es|ed)?\b', r'\bfreez(?:e|ing|es|ed)?\b',
        r'\blag(?:ging)?\b', r'\bslow\b', r'\bkeyboard\b', r'\btyping\b', r'\bopen(?:ing)?\b',
        r'\bstore\b', r'\bdownload(?:ing)?\b'
    ]
}


def rule_match_intent(text: str) -> Tuple[str, float]:
    """
    Classifies a customer text into an intent based on keyword match density.
    Returns (intent_name, score). Falls back to 'other_general' if low match.
    """
    text_lower = text.lower()
    scores = {}

    for intent, patterns in INTENT_KEYWORD_PATTERNS.items():
        match_count = sum(1 for p in patterns if re.search(p, text_lower))
        if match_count > 0:
            scores[intent] = match_count

    if not scores:
        return "other_general", 0.50

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]
    # Normalize pseudo-confidence
    confidence = min(0.60 + (best_score * 0.12), 0.96)
    return best_intent, round(confidence, 2)


class IntentDiscovery:
    def __init__(self, train_path: Path = TRAIN_DATA_PATH):
        self.train_path = train_path

    def analyze_dataset_intents(self) -> Dict[str, Any]:
        """
        Loads training conversations, discovers high-frequency n-grams and intents,
        and computes empirical distribution and representative examples.
        """
        if not self.train_path.exists():
            raise FileNotFoundError(f"Training conversations not found at {self.train_path}")

        with open(self.train_path, "r", encoding="utf-8") as f:
            train_convs = json.load(f)

        messages = [c["incoming_query"] for c in train_convs]

        # Extract top TF-IDF n-grams
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=50)
        tfidf_matrix = vectorizer.fit_transform(messages)
        top_terms = vectorizer.get_feature_names_out().tolist()

        # Classify each training query
        labeled_intents = []
        intent_examples: Dict[str, List[str]] = {k: [] for k in INTENT_DEFINITIONS}

        for conv in train_convs:
            intent, conf = rule_match_intent(conv["incoming_query"])
            labeled_intents.append(intent)
            if len(intent_examples[intent]) < 5:
                intent_examples[intent].append(conv["incoming_query"])

        total = len(labeled_intents)
        counts = Counter(labeled_intents)
        distribution = {k: round(v / total, 4) for k, v in counts.items()}

        result = {
            "total_messages": total,
            "top_ngrams": top_terms[:20],
            "intent_distribution": distribution,
            "intent_counts": dict(counts),
            "representative_examples": intent_examples
        }
        return result


if __name__ == "__main__":
    discovery = IntentDiscovery()
    stats = discovery.analyze_dataset_intents()
    print("Dataset Intent Distribution:")
    for intent, pct in stats["intent_distribution"].items():
        count = stats["intent_counts"][intent]
        print(f"  {intent}: {count} ({pct * 100:.1f}%)")
