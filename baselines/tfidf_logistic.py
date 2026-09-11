import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)
from src.config import TRAIN_DATA_PATH, GOLDEN_SET_PATH, CONFUSION_MATRIX_PATH, RESULTS_DIR
from src.intent_discovery import rule_match_intent

class TfidfLogisticBaseline:
    _cached_vectorizer = None
    _cached_classifier = None
    _cached_classes = None

    def __init__(self, train_path: Path = TRAIN_DATA_PATH):
        self.train_path = train_path
        if TfidfLogisticBaseline._cached_vectorizer is not None:
            self.vectorizer = TfidfLogisticBaseline._cached_vectorizer
            self.classifier = TfidfLogisticBaseline._cached_classifier
            self.classes_ = TfidfLogisticBaseline._cached_classes
            self.is_fitted = True
        else:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_features=5000,
                sublinear_tf=True
            )
            self.classifier = LogisticRegression(
                C=1.0,
                max_iter=1000,
                class_weight="balanced",
                random_state=42
            )
            self.is_fitted = False
            self.classes_: List[str] = []

    def fit(self):
        if self.is_fitted and TfidfLogisticBaseline._cached_vectorizer is not None:
            return self

        with open(self.train_path, "r", encoding="utf-8") as f:
            train_convs = json.load(f)

        X_train = [c["incoming_query"] for c in train_convs]
        y_train = [rule_match_intent(c["incoming_query"])[0] for c in train_convs]

        X_train_vec = self.vectorizer.fit_transform(X_train)
        self.classifier.fit(X_train_vec, y_train)
        self.classes_ = list(self.classifier.classes_)
        self.is_fitted = True

        # Cache class level
        TfidfLogisticBaseline._cached_vectorizer = self.vectorizer
        TfidfLogisticBaseline._cached_classifier = self.classifier
        TfidfLogisticBaseline._cached_classes = self.classes_
        return self

    def predict(self, texts: List[str]) -> List[str]:
        if not self.is_fitted:
            self.fit()
        vecs = self.vectorizer.transform(texts)
        return self.classifier.predict(vecs).tolist()

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        if not self.is_fitted:
            self.fit()
        vecs = self.vectorizer.transform(texts)
        return self.classifier.predict_proba(vecs)

    def evaluate(self, golden_path: Path = GOLDEN_SET_PATH, save_artifacts: bool = True) -> Dict[str, Any]:
        if not self.is_fitted:
            self.fit()

        df = pd.read_csv(golden_path)
        y_true = df["intent"].tolist()
        texts = df["customer_message"].tolist()
        y_pred = self.predict(texts)

        acc = accuracy_score(y_true, y_pred)
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average="macro", zero_division=0
        )
        report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=self.classes_)

        results = {
            "model": "TF-IDF + Logistic Regression",
            "accuracy": round(float(acc), 4),
            "macro_precision": round(float(p_macro), 4),
            "macro_recall": round(float(r_macro), 4),
            "macro_f1": round(float(f1_macro), 4),
            "classes": self.classes_,
            "confusion_matrix": cm.tolist(),
            "per_class": {
                cls_name: {
                    "precision": round(float(metrics.get("precision", 0)), 4),
                    "recall": round(float(metrics.get("recall", 0)), 4),
                    "f1": round(float(metrics.get("f1-score", 0)), 4),
                    "support": int(metrics.get("support", 0))
                }
                for cls_name, metrics in report_dict.items()
                if cls_name in self.classes_
            }
        }

        if save_artifacts:
            self._save_confusion_matrix_plot(cm, self.classes_)

        return results

    def _save_confusion_matrix_plot(self, cm: np.ndarray, labels: List[str]):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
            ax.figure.colorbar(im, ax=ax)

            ax.set(
                xticks=np.arange(cm.shape[1]),
                yticks=np.arange(cm.shape[0]),
                xticklabels=labels,
                yticklabels=labels,
                title="Confusion Matrix: TF-IDF + Logistic Regression",
                ylabel="True Intent",
                xlabel="Predicted Intent"
            )
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            thresh = cm.max() / 2.0
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, format(cm[i, j], "d"),
                            ha="center", va="center",
                            color="white" if cm[i, j] > thresh else "black")
            fig.tight_layout()
            CONFUSION_MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(CONFUSION_MATRIX_PATH, dpi=150)
            plt.close()
        except Exception as e:
            print(f"Notice: Matplotlib plot generation encountered: {e}")


if __name__ == "__main__":
    baseline = TfidfLogisticBaseline()
    metrics = baseline.evaluate()
    print("TF-IDF + Logistic Regression Results:")
    print(f"  Accuracy: {metrics['accuracy']}")
    print(f"  Macro F1: {metrics['macro_f1']}")
    print("  Per-class metrics:")
    for cls_name, vals in metrics["per_class"].items():
        print(f"    {cls_name}: F1={vals['f1']} (P={vals['precision']}, R={vals['recall']}, N={vals['support']})")
