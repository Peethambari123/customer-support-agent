import re
import html
from typing import Optional, Dict, Any
import pandas as pd

# Regular expressions for PII and entity sanitization
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
ACCOUNT_ID_REGEX = re.compile(r'@\d{4,8}\b')  # Anonymized Twitter handle numbers in Kaggle dataset (e.g. @115854)
WHITESPACE_REGEX = re.compile(r'\s+')


def clean_text(text: Optional[str], mask_pii: bool = True) -> str:
    """
    Cleans, unescapes, and optionally sanitizes customer and agent tweet text.
    Handles HTML entities, Twitter artifacts, and PII masking.
    """
    if not isinstance(text, str):
        return ""
    
    # Unescape HTML entities (&gt;, &lt;, &amp;)
    cleaned = html.unescape(text)
    
    # Mask URLs to prevent phishing links or session leakage
    cleaned = URL_REGEX.sub("[LINK]", cleaned)
    
    if mask_pii:
        # Mask emails
        cleaned = EMAIL_REGEX.sub("[EMAIL]", cleaned)
        # Mask phone numbers
        cleaned = PHONE_REGEX.sub("[PHONE]", cleaned)
        # Mask numeric customer IDs
        cleaned = ACCOUNT_ID_REGEX.sub("@customer", cleaned)
    
    # Normalize multiple whitespace, tabs, and newlines
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned).strip()
    return cleaned


def is_valid_message(text: Optional[str]) -> bool:
    """Returns True if text contains substantive characters beyond whitespace/links."""
    if not isinstance(text, str):
        return False
    stripped = text.strip()
    if len(stripped) < 3:
        return False
    if stripped.lower() in {"null", "nan", "none", "deleted"}:
        return False
    # Check if tweet only contains a link or a mention
    tokens = stripped.split()
    non_entity_tokens = [t for t in tokens if not t.startswith("@") and not t.startswith("http")]
    return len(non_entity_tokens) > 0


def parse_timestamp(ts_val: Any) -> Optional[pd.Timestamp]:
    """
    Parses Twitter formatted timestamps into standard UTC Timestamps.
    Example format: 'Tue Oct 31 22:10:47 +0000 2017'
    """
    if pd.isna(ts_val):
        return None
    try:
        return pd.to_datetime(ts_val, errors="coerce")
    except Exception:
        return None
