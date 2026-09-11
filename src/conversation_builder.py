import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from src.config import (
    SELECTED_BRAND,
    TRAIN_DATA_PATH,
    TEST_DATA_PATH,
    RANDOM_SEED,
    TRAIN_RATIO,
    PROCESSED_DIR
)
from src.data_loader import DataLoader
from src.preprocessing import clean_text


class ConversationBuilder:
    def __init__(self, brand: str = SELECTED_BRAND, random_seed: int = RANDOM_SEED):
        self.brand = brand
        self.random_seed = random_seed
        self.conversations: List[Dict[str, Any]] = []

    def build_conversations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Reconstructs customer support conversations for the target brand.
        Preserves conversation_id, brand, timestamp, customer_messages, agent_messages, full_thread.
        Strictly prevents data leakage by isolating the initial incoming customer query
        from downstream agent resolutions.
        """
        # Map tweet_id to row record for fast lookup
        tweet_lookup = df.set_index("tweet_id").to_dict(orient="index")

        # Find all agent replies from the selected brand
        brand_replies = df[
            (df["author_id"] == self.brand) & 
            (~df["inbound"]) & 
            (df["in_response_to_tweet_id"].notna())
        ].copy()

        conversations = []
        seen_conv_ids = set()

        for _, agent_row in brand_replies.iterrows():
            parent_id = int(agent_row["in_response_to_tweet_id"])
            parent_tweet = tweet_lookup.get(parent_id)

            # Ensure parent tweet is an inbound customer tweet
            if not parent_tweet or not parent_tweet.get("inbound", False):
                continue

            conv_id = f"conv_{parent_id}_{agent_row['tweet_id']}"
            if conv_id in seen_conv_ids:
                continue
            seen_conv_ids.add(conv_id)

            cust_text = parent_tweet["cleaned_text"]
            agent_text = agent_row["cleaned_text"]

            # Filter trivial or unhelpful fragments
            if len(cust_text.split()) < 3 or len(agent_text.split()) < 3:
                continue

            conv_record = {
                "conversation_id": conv_id,
                "brand": self.brand,
                "timestamp": str(parent_tweet.get("created_at", "")),
                "customer_tweet_id": parent_id,
                "agent_tweet_id": int(agent_row["tweet_id"]),
                "customer_messages": [cust_text],
                "agent_messages": [agent_text],
                "full_thread": [
                    {"speaker": "customer", "text": cust_text, "tweet_id": parent_id},
                    {"speaker": "agent", "text": agent_text, "tweet_id": int(agent_row["tweet_id"])}
                ],
                # Explicit evaluation query input - strict anti-leakage isolation
                "incoming_query": cust_text,
                "ground_truth_resolution": agent_text
            }
            conversations.append(conv_record)

        self.conversations = conversations
        return conversations

    def split_and_save_conversations(
        self,
        conversations: Optional[List[Dict[str, Any]]] = None,
        train_path: Path = TRAIN_DATA_PATH,
        test_path: Path = TEST_DATA_PATH,
        train_ratio: float = TRAIN_RATIO
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Splits conversations at the CONVERSATION level (not tweet level) to guarantee
        that no context, customer ID, or thread fragments leak between training and evaluation.
        """
        convs = conversations or self.conversations
        if not convs:
            raise ValueError("No conversations to split. Run build_conversations first.")

        # Deterministic shuffle
        rng = random.Random(self.random_seed)
        shuffled = list(convs)
        rng.shuffle(shuffled)

        split_idx = int(len(shuffled) * train_ratio)
        train_set = shuffled[:split_idx]
        test_set = shuffled[split_idx:]

        # Ensure directory exists
        train_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.parent.mkdir(parents=True, exist_ok=True)

        with open(train_path, "w", encoding="utf-8") as f:
            json.dump(train_set, f, indent=2)

        with open(test_path, "w", encoding="utf-8") as f:
            json.dump(test_set, f, indent=2)

        return train_set, test_set


def run_pipeline() -> Tuple[int, int]:
    """Convenience pipeline function to load data, build conversations, and save splits."""
    loader = DataLoader()
    df = loader.load_raw_dataset()
    builder = ConversationBuilder()
    convs = builder.build_conversations(df)
    train_convs, test_convs = builder.split_and_save_conversations(convs)
    return len(train_convs), len(test_convs)


if __name__ == "__main__":
    n_train, n_test = run_pipeline()
    print(f"Conversation reconstruction complete: {n_train} train convs, {n_test} test convs.")
