import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from src.config import GOLDEN_SET_PATH
from baselines.majority import MajorityBaseline
from baselines.tfidf_logistic import TfidfLogisticBaseline
from src.intent_classifier import AIIntentClassifier


def run_intent_evaluation(golden_path: Path = GOLDEN_SET_PATH) -> Dict[str, Any]:
    """
    Evaluates intent classification across Majority, TF-IDF Logistic, and AI Classifier
    on the 200-sample hand-verified golden evaluation set.
    """
    df = pd.read_csv(golden_path)
    y_true = df["intent"].tolist()
    texts = df["customer_message"].tolist()

    # 1. Majority Baseline
    majority_model = MajorityBaseline().fit()
    y_pred_maj = majority_model.predict(texts)
    maj_acc = accuracy_score(y_true, y_pred_maj)
    maj_p, maj_r, maj_f1, _ = precision_recall_fscore_support(y_true, y_pred_maj, average="macro", zero_division=0)

    # 2. TF-IDF + Logistic Regression
    tfidf_model = TfidfLogisticBaseline().fit()
    y_pred_tfidf = tfidf_model.predict(texts)
    tfidf_acc = accuracy_score(y_true, y_pred_tfidf)
    tfidf_p, tfidf_r, tfidf_f1, _ = precision_recall_fscore_support(y_true, y_pred_tfidf, average="macro", zero_division=0)

    # 3. AI Classifier
    ai_model = AIIntentClassifier()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        ai_preds = list(executor.map(ai_model.classify, texts))
    y_pred_ai = [p["intent"] for p in ai_preds]
    ai_acc = accuracy_score(y_true, y_pred_ai)
    ai_p, ai_r, ai_f1, _ = precision_recall_fscore_support(y_true, y_pred_ai, average="macro", zero_division=0)

    return {
        "dataset": "golden_set_200",
        "sample_size": len(df),
        "majority_baseline": {
            "accuracy": round(float(maj_acc), 4),
            "macro_precision": round(float(maj_p), 4),
            "macro_recall": round(float(maj_r), 4),
            "macro_f1": round(float(maj_f1), 4)
        },
        "tfidf_logistic_baseline": {
            "accuracy": round(float(tfidf_acc), 4),
            "macro_precision": round(float(tfidf_p), 4),
            "macro_recall": round(float(tfidf_r), 4),
            "macro_f1": round(float(tfidf_f1), 4)
        },
        "ai_intent_classifier": {
            "accuracy": round(float(ai_acc), 4),
            "macro_precision": round(float(ai_p), 4),
            "macro_recall": round(float(ai_r), 4),
            "macro_f1": round(float(ai_f1), 4)
        }
    }


if __name__ == "__main__":
    results = run_intent_evaluation()
    print("Intent Evaluation Summary:")
    print(json.dumps(results, indent=2))
