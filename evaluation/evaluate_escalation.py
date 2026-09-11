import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from src.config import GOLDEN_SET_PATH
from src.intent_classifier import AIIntentClassifier
from src.retrieval import HistoricalRetriever
from src.escalation import EscalationEngine


def run_escalation_evaluation(golden_path: Path = GOLDEN_SET_PATH) -> Dict[str, Any]:
    """
    Evaluates escalation safety decisions against hand-verified golden set.
    Includes comprehensive business cost analysis for false negatives vs false positives.
    """
    df = pd.read_csv(golden_path)
    y_true = df["escalate"].astype(int).tolist()
    texts = df["customer_message"].tolist()

    classifier = AIIntentClassifier()
    retriever = HistoricalRetriever().build_index()
    escalation_engine = EscalationEngine()

    y_pred = []
    reasons = []

    for text in texts:
        clf_res = classifier.classify(text)
        ret_res = retriever.retrieve(text, top_k=3)
        ev_res = retriever.assess_evidence_sufficiency(ret_res)
        esc_res = escalation_engine.evaluate(text, clf_res, ev_res)

        pred_code = 1 if esc_res["decision"] == "ESCALATE" else 0
        y_pred.append(pred_code)
        reasons.append(esc_res["reason"])

    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", pos_label=1, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    # cm: [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = cm.ravel()

    # Business impact cost modeling
    # Over-escalation (FP) costs human advisor time (~$5.00 per unnecessary ticket)
    # Under-escalation (FN) risks security breach, legal claim, or severe customer churn (~$50.00 per missed risk)
    COST_PER_FP = 5.00
    COST_PER_FN = 50.00

    total_pipeline_risk_cost = (fp * COST_PER_FP) + (fn * COST_PER_FN)
    all_human_cost = len(y_true) * COST_PER_FP
    all_automated_cost = sum(y_true) * COST_PER_FN

    cost_savings = all_human_cost - total_pipeline_risk_cost

    return {
        "dataset": "golden_set_200",
        "total_samples": len(y_true),
        "ground_truth_escalations": int(sum(y_true)),
        "ground_truth_autohandle": int(len(y_true) - sum(y_true)),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4),
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
            "over_escalation_rate": round(float(fp / max(tn + fp, 1)), 4),
            "missed_escalation_rate": round(float(fn / max(fn + tp, 1)), 4)
        },
        "business_cost_analysis": {
            "cost_per_false_positive_usd": COST_PER_FP,
            "cost_per_false_negative_usd": COST_PER_FN,
            "pipeline_total_cost_usd": round(total_pipeline_risk_cost, 2),
            "baseline_100pct_human_cost_usd": round(all_human_cost, 2),
            "baseline_zero_escalation_risk_cost_usd": round(all_automated_cost, 2),
            "net_savings_over_human_usd": round(cost_savings, 2),
            "automation_containment_rate": round(float(tn / len(y_true)), 4)
        }
    }


if __name__ == "__main__":
    results = run_escalation_evaluation()
    print("Escalation Evaluation Summary:")
    print(json.dumps(results, indent=2))
