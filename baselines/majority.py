import json
from collections import Counter
from typing import Dict, Any, List
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from src.config import TRAIN_DATA_PATH, GOLDEN_SET_PATH
from src.intent_discovery import rule_match_intent


class MajorityBaseline:
    def __init__(self, train_path=TRAIN_DATA_PATH):
        self.train_path = train_path
        self.majority_class: str = "other_general"

    def fit(self):
        with open(self.train_path, "r", encoding="utf-8") as f:
            train_convs = json.load(f)
        intents = [rule_match_intent(c["incoming_query"])[0] for c in train_convs]
        counts = Counter(intents)
        self.majority_class = counts.most_common(1)[0][0]
        return self

    def predict(self, texts: List[str]) -> List[str]:
        return [self.majority_class] * len(texts)

    def evaluate(self, golden_path=GOLDEN_SET_PATH) -> Dict[str, Any]:
        self.fit()
        df = pd.read_csv(golden_path)
        y_true = df["intent"].tolist()
        y_pred = self.predict(df["customer_message"].tolist())

        acc = accuracy_score(y_true, y_pred)
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average="macro", zero_division=0
        )

        return {
            "model": "Majority Baseline",
            "majority_class": self.majority_class,
            "accuracy": round(float(acc), 4),
            "macro_precision": round(float(p_macro), 4),
            "macro_recall": round(float(r_macro), 4),
            "macro_f1": round(float(f1_macro), 4)
        }


if __name__ == "__main__":
    baseline = MajorityBaseline()
    metrics = baseline.evaluate()
    print("Majority Baseline Results:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
