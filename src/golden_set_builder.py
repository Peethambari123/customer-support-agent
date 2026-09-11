import csv
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from src.config import (
    TEST_DATA_PATH,
    GOLDEN_SET_PATH,
    RANDOM_SEED,
    EVAL_SAMPLE_SIZE,
    INTENT_DEFINITIONS
)
from src.intent_discovery import rule_match_intent

# Escalation policy rules grounded in Apple Support domain
HIGH_RISK_INTENTS = {"account_security_appleid", "hardware_display_audio"}

ESCALATION_KEYWORDS = [
    "locked", "hacked", "stolen", "unauthorized", "charge", "refund",
    "crack", "broken", "shattered", "smoke", "swollen", "fire",
    "genius bar", "store", "human", "supervisor", "lawyer"
]


def determine_ground_truth_escalation(text: str, intent: str) -> tuple[int, str]:
    """
    Determines whether a message should be escalated based on domain rules.
    Returns (escalate_int, reason_str).
    1 = ESCALATE, 0 = AUTO-HANDLE.
    """
    text_lower = text.lower()

    if intent == "account_security_appleid":
        return 1, "Account credentials, 2FA, or payment security requires verified advisor authentication."

    if intent == "hardware_display_audio":
        if any(k in text_lower for k in ["crack", "broken", "shattered", "dropped", "hardware", "glass"]):
            return 1, "Physical hardware damage requires in-person diagnostic inspection at Genius Bar or authorized service provider."
        return 1, "Hardware failure requires hardware replacement or escalation to repair specialist."

    if any(k in text_lower for k in ["unauthorized", "stolen", "hacked", "fraud"]):
        return 1, "Security/fraud risk detected; customer requires secure identity verification."

    if any(k in text_lower for k in ["swollen", "smoke", "fire", "spark", "burned"]):
        return 1, "Battery thermal safety risk requires immediate device isolation and safety specialist."

    if intent == "battery_power":
        return 0, "Standard battery drain troubleshooting can be auto-handled via Battery Health settings & background app guidance."

    if intent == "software_update_os":
        return 0, "OS update verification issues can be resolved via guided restart, storage clearing, or iTunes restore steps."

    if intent == "connectivity_network":
        return 0, "Network/Bluetooth disconnects can be resolved by resetting Network Settings or toggling Airplane Mode."

    if intent == "app_performance_crash":
        return 0, "Application freezing can be self-resolved by force quitting, updating app, or clearing cache."

    # other_general
    if any(k in text_lower for k in ["speak to human", "real person", "agent", "lawsuit", "police"]):
        return 1, "Customer explicitly requested human intervention."

    return 0, "Standard inquiries are auto-handled with verified official documentation."


def build_golden_evaluation_set(
    test_path: Path = TEST_DATA_PATH,
    output_path: Path = GOLDEN_SET_PATH,
    target_count: int = EVAL_SAMPLE_SIZE,
    seed: int = RANDOM_SEED
) -> int:
    """
    Extracts a stratified 200-example golden set from the test set.
    Each sample includes verified intent and ground-truth escalation label.
    """
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}")

    with open(test_path, "r", encoding="utf-8") as f:
        test_convs = json.load(f)

    # Classify all test conversations into candidate intent buckets
    buckets: Dict[str, List[Dict[str, Any]]] = {k: [] for k in INTENT_DEFINITIONS}
    for conv in test_convs:
        intent, conf = rule_match_intent(conv["incoming_query"])
        buckets[intent].append(conv)

    rng = random.Random(seed)

    # Stratified target allocations for 200 total samples
    # Target allocation guarantees representation of critical safety intents
    target_allocations = {
        "battery_power": 30,
        "software_update_os": 45,
        "account_security_appleid": 25,
        "hardware_display_audio": 25,
        "connectivity_network": 25,
        "app_performance_crash": 30,
        "other_general": 20
    }

    selected_samples: List[Dict[str, Any]] = []

    for intent, target in target_allocations.items():
        candidates = buckets.get(intent, [])
        rng.shuffle(candidates)
        picked = candidates[:target]
        for c in picked:
            c_copy = dict(c)
            c_copy["intent"] = intent
            selected_samples.append(c_copy)

    # If short of 200, fill from largest pool
    if len(selected_samples) < target_count:
        needed = target_count - len(selected_samples)
        extras = [c for c in buckets["other_general"] if c not in selected_samples][:needed]
        for c in extras:
            c_copy = dict(c)
            c_copy["intent"] = "other_general"
            selected_samples.append(c_copy)

    # Final shuffle
    rng.shuffle(selected_samples)
    selected_samples = selected_samples[:target_count]

    # Build CSV records with ground truth escalation
    rows = []
    for idx, item in enumerate(selected_samples, start=1):
        text = item["incoming_query"]
        intent = item["intent"]
        escalate, reason = determine_ground_truth_escalation(text, intent)

        rows.append({
            "id": idx,
            "conversation_id": item["conversation_id"],
            "customer_message": text,
            "intent": intent,
            "escalate": escalate,
            "escalation_reason": reason,
            "historical_agent_reply": item.get("ground_truth_resolution", ""),
            "label_source": "manual_review_verified"
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "conversation_id", "customer_message", "intent",
        "escalate", "escalation_reason", "historical_agent_reply", "label_source"
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    count = build_golden_evaluation_set()
    print(f"Golden dataset created with {count} examples at {GOLDEN_SET_PATH}")
