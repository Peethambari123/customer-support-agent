import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
from src.config import RAW_SAMPLE_PATH, DATA_DIR, SELECTED_BRAND
from src.preprocessing import clean_text, is_valid_message, parse_timestamp

EXPECTED_COLUMN_ALIASES = {
    "tweet_id": ["tweet_id", "id", "tweetid", "id_str"],
    "author_id": ["author_id", "author", "user", "screen_name", "from_user"],
    "inbound": ["inbound", "is_inbound", "in_bound", "customer_message"],
    "created_at": ["created_at", "timestamp", "date", "time", "created_date"],
    "text": ["text", "tweet", "message", "tweet_text", "content"],
    "response_tweet_id": ["response_tweet_id", "response_id", "reply_tweet_id"],
    "in_response_to_tweet_id": ["in_response_to_tweet_id", "parent_tweet_id", "in_reply_to_tweet_id", "reply_to_id"]
}


class DataLoader:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = Path(file_path) if file_path else RAW_SAMPLE_PATH
        self.column_map: Dict[str, str] = {}
        self.df: Optional[pd.DataFrame] = None
        self._brand_table_cache: Optional[pd.DataFrame] = None

    def inspect_and_resolve_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """Maps arbitrary CSV headers to standard normalized column names."""
        resolved = {}
        lower_cols = {c.lower().strip(): c for c in df_columns}
        
        for std_name, aliases in EXPECTED_COLUMN_ALIASES.items():
            found = False
            for alias in aliases:
                if alias in lower_cols:
                    resolved[std_name] = lower_cols[alias]
                    found = True
                    break
            if not found:
                resolved[std_name] = None
        return resolved

    def load_raw_dataset(self) -> pd.DataFrame:
        """
        Loads CSV dataset, auto-resolves schema, removes duplicates and malformed rows,
        and standardizes data types.
        """
        if self.df is not None:
            return self.df

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.file_path}. Please place 'twcs_sample.csv' "
                f"or 'twcs.csv' in '{self.file_path.parent}'."
            )

        # Robust CSV load handling bad lines
        df = pd.read_csv(self.file_path, on_bad_lines="skip", low_memory=False)
        self.column_map = self.inspect_and_resolve_columns(df.columns.tolist())

        # Verify critical columns
        required = ["tweet_id", "author_id", "inbound", "text"]
        missing = [r for r in required if not self.column_map.get(r)]
        if missing:
            raise ValueError(f"Missing essential columns {missing} in dataset at {self.file_path}")

        # Rename to canonical column names
        rename_dict = {orig: std for std, orig in self.column_map.items() if orig}
        df = df.rename(columns=rename_dict)

        # Deduplicate on tweet_id
        df = df.drop_duplicates(subset=["tweet_id"])
        
        # Standardize inbound as boolean
        if df["inbound"].dtype != bool:
            df["inbound"] = df["inbound"].astype(str).str.lower().isin(["true", "1", "t", "yes"])

        # Filter empty / deleted text
        df["cleaned_text"] = df["text"].apply(lambda t: clean_text(t, mask_pii=True))
        df["is_valid"] = df["text"].apply(is_valid_message)
        df = df[df["is_valid"]].copy()

        # Parse timestamps safely
        if "created_at" in df.columns:
            df["parsed_timestamp"] = df["created_at"].apply(parse_timestamp)

        self.df = df
        return df

    def generate_brand_analysis_table(self, top_n: int = 8) -> pd.DataFrame:
        """
        Measurable brand selection analysis.
        Computes Conversations, Customer Tweets, and Agent Tweets for top brands.
        Uses fast dictionary indexing.
        """
        if self._brand_table_cache is not None:
            return self._brand_table_cache

        if self.df is None:
            self.load_raw_dataset()
        df = self.df

        # Fast lookup map for inbound status
        inbound_map = dict(zip(df["tweet_id"], df["inbound"]))

        # Agent tweets are author_id where inbound == False
        agent_tweets_df = df[df["inbound"] == False]
        top_brand_names = agent_tweets_df["author_id"].value_counts().head(top_n).index.tolist()

        table_rows = []
        for brand in top_brand_names:
            brand_agents = df[(df["author_id"] == brand) & (~df["inbound"])]
            agent_count = len(brand_agents)
            
            # Customer mentions
            cust_mention_count = len(df[(df["inbound"]) & (df["text"].str.contains(f"@{brand}", case=False, na=False))])
            
            # Count clean conversation pairs using fast map lookup
            parent_ids = brand_agents["in_response_to_tweet_id"].dropna().astype(int)
            conv_count = sum(1 for pid in parent_ids if inbound_map.get(pid) is True)

            table_rows.append({
                "Brand": brand,
                "Conversations": conv_count,
                "Customer Tweets": cust_mention_count,
                "Agent Tweets": agent_count,
                "Usability Score": round((conv_count * 1.5 + cust_mention_count) / 1000, 2)
            })

        summary_df = pd.DataFrame(table_rows).sort_values(by="Conversations", ascending=False).reset_index(drop=True)
        self._brand_table_cache = summary_df
        return summary_df
