import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import (
    TRAIN_DATA_PATH,
    RETRIEVAL_TOP_K,
    SIMILARITY_THRESHOLD
)
from src.intent_discovery import rule_match_intent


class HistoricalRetriever:
    _cached_vectorizer = None
    _cached_matrix = None
    _cached_records = None

    def __init__(
        self,
        train_path: Path = TRAIN_DATA_PATH,
        top_k: int = RETRIEVAL_TOP_K,
        similarity_threshold: float = SIMILARITY_THRESHOLD
    ):
        self.train_path = train_path
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        if HistoricalRetriever._cached_matrix is not None:
            self.vectorizer = HistoricalRetriever._cached_vectorizer
            self.tfidf_matrix = HistoricalRetriever._cached_matrix
            self.training_records = HistoricalRetriever._cached_records
            self.is_indexed = True
        else:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_features=10000,
                sublinear_tf=True
            )
            self.training_records: List[Dict[str, Any]] = []
            self.tfidf_matrix = None
            self.is_indexed = False

    def build_index(self):
        """Indexes only the training conversations to strictly prevent test leakage."""
        if self.is_indexed and HistoricalRetriever._cached_matrix is not None:
            return self

        cache_file = self.train_path.parent / "retrieval_index.pkl"
        import pickle
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)
                self.vectorizer = cached_data["vectorizer"]
                self.tfidf_matrix = cached_data["matrix"]
                self.training_records = cached_data["records"]
                self.is_indexed = True
                HistoricalRetriever._cached_vectorizer = self.vectorizer
                HistoricalRetriever._cached_matrix = self.tfidf_matrix
                HistoricalRetriever._cached_records = self.training_records
                return self
            except Exception:
                pass

        if not self.train_path.exists():
            raise FileNotFoundError(f"Training conversations not found at {self.train_path}")

        with open(self.train_path, "r", encoding="utf-8") as f:
            self.training_records = json.load(f)

        queries = [r["incoming_query"] for r in self.training_records]
        self.tfidf_matrix = self.vectorizer.fit_transform(queries)
        self.is_indexed = True

        HistoricalRetriever._cached_vectorizer = self.vectorizer
        HistoricalRetriever._cached_matrix = self.tfidf_matrix
        HistoricalRetriever._cached_records = self.training_records

        try:
            with open(cache_file, "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "matrix": self.tfidf_matrix,
                    "records": self.training_records
                }, f)
        except Exception:
            pass

        return self

    def retrieve(self, query_text: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves top-k historical conversations most similar to the incoming customer issue.
        Returns list of structured match objects with similarity scores.
        """
        if not self.is_indexed:
            self.build_index()

        k = top_k or self.top_k
        query_vec = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            sim = float(similarities[idx])
            rec = self.training_records[idx]
            inferred_intent, _ = rule_match_intent(rec["incoming_query"])

            results.append({
                "conversation_id": rec["conversation_id"],
                "customer_issue": rec["incoming_query"],
                "historical_agent_response": rec.get("ground_truth_resolution", ""),
                "similarity_score": round(sim, 4),
                "intent": inferred_intent,
                "timestamp": rec.get("timestamp", "")
            })

        return results

    def assess_evidence_sufficiency(self, retrieved: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates whether retrieved historical evidence is strong enough for automated resolution."""
        if not retrieved:
            return {
                "sufficient": False,
                "max_similarity": 0.0,
                "reason": "No historical conversations retrieved."
            }

        max_sim = retrieved[0]["similarity_score"]
        sufficient = max_sim >= self.similarity_threshold

        return {
            "sufficient": sufficient,
            "max_similarity": max_sim,
            "threshold": self.similarity_threshold,
            "reason": (
                f"Historical similarity score {max_sim:.2f} meets threshold {self.similarity_threshold:.2f}"
                if sufficient else
                f"Historical similarity score {max_sim:.2f} is below minimum grounding threshold {self.similarity_threshold:.2f}"
            )
        }


if __name__ == "__main__":
    retriever = HistoricalRetriever()
    retriever.build_index()
    test_q = "@AppleSupport my iPhone screen went black after dropping it"
    matches = retriever.retrieve(test_q, top_k=3)
    evidence = retriever.assess_evidence_sufficiency(matches)
    print(f"Query: {test_q}")
    print(f"Evidence Sufficient: {evidence['sufficient']} (Max Sim: {evidence['max_similarity']})")
    for i, m in enumerate(matches, start=1):
        print(f"\nMatch #{i} [Sim: {m['similarity_score']}] (Conv: {m['conversation_id']}):")
        print(f"  Customer: {m['customer_issue']}")
        print(f"  Historical Agent: {m['historical_agent_response']}")
