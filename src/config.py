import os
import socket
from pathlib import Path

# Ensure IPv4 resolution is prioritized in container environment
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_first_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    res = _orig_getaddrinfo(host, port, family, type, proto, flags)
    return sorted(res, key=lambda x: 0 if x[0] == socket.AF_INET else 1)
socket.getaddrinfo = _ipv4_first_getaddrinfo

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
CONFIG_DIR = PROJECT_ROOT / "config"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORT_DIR = PROJECT_ROOT / "report"

# Data Files
RAW_SAMPLE_PATH = SAMPLE_DIR / "twcs_sample.csv"
TRAIN_DATA_PATH = PROCESSED_DIR / "train_conversations.json"
TEST_DATA_PATH = PROCESSED_DIR / "test_conversations.json"
GOLDEN_SET_PATH = DATA_DIR / "golden_set.csv"
INTENTS_CONFIG_PATH = CONFIG_DIR / "intents.json"
DATA_INTENTS_PATH = DATA_DIR / "intents.json"
METRICS_PATH = RESULTS_DIR / "metrics.json"
FAILURE_ANALYSIS_PATH = RESULTS_DIR / "failure_analysis.json"
CONFUSION_MATRIX_PATH = RESULTS_DIR / "confusion_matrix.png"

# Brand Configuration
SELECTED_BRAND = "AppleSupport"
BRAND_SELECTION_REASON = (
    "Selected AppleSupport after data inspection because it features 3,979 clean customer-agent "
    "conversation threads in the reproducible sample (99.2% English), high issue diversity across "
    "hardware, software, battery, and account security, and an iconic, highly standardized support "
    "style ideal for grounded retrieval and safety-critical escalation."
)

# Deterministic Seed & Splits
RANDOM_SEED = 42
TRAIN_RATIO = 0.80
EVAL_SAMPLE_SIZE = 200
HUMAN_EVAL_SAMPLE_SIZE = 30

# Model Configurations
EMBEDDING_MODEL_NAME = "tfidf-vectorizer"  # Lightweight, reproducible, zero-external-download
GEMINI_MODEL = "gemini-3.6-flash"
RETRIEVAL_TOP_K = 3
SIMILARITY_THRESHOLD = 0.18
CONFIDENCE_THRESHOLD = 0.65

# Intent Taxonomy Definition
INTENT_DEFINITIONS = {
    "battery_power": {
        "name": "Battery & Power Management",
        "description": "Issues concerning battery drain, overheating, charging failures, or unexpected shutdowns.",
        "examples": [
            "My iPhone battery drops from 80% to 10% in an hour after the update.",
            "iPhone 7 plus gets extremely hot while charging.",
            "Phone won't turn on even when plugged in for hours."
        ],
        "default_escalate": False,
        "historical_action": "Inquire about battery health percentage (Settings > Battery > Battery Health) and charging accessories."
    },
    "software_update_os": {
        "name": "OS & Software Updates",
        "description": "Problems installing, downloading, or verifying iOS/macOS updates, or system glitches post-update.",
        "examples": [
            "Update to iOS 11.1 keeps failing with error 3194.",
            "My phone is stuck on the Apple logo after updating.",
            "Unable to download iOS update, says storage is full even though I have 10GB free."
        ],
        "default_escalate": False,
        "historical_action": "Guide user to restart device, free up local storage, or update via iTunes/Finder."
    },
    "account_security_appleid": {
        "name": "Apple ID & Account Security",
        "description": "Locked Apple ID, forgotten passwords, two-factor authentication failures, or unauthorized purchases.",
        "examples": [
            "My Apple ID is locked for security reasons and I can't receive the verification code.",
            "Someone hacked my iCloud account and changed the trusted phone number.",
            "I see an unauthorized charge on my account from iTunes."
        ],
        "default_escalate": True,
        "historical_action": "Prompt customer to visit iforgot.apple.com or transition to private DM/support advisor for identity verification."
    },
    "hardware_display_audio": {
        "name": "Hardware, Display & Audio",
        "description": "Physical damage, cracked screens, unresponsive touchscreen digitizers, distorted speakers, or camera failure.",
        "examples": [
            "Dropped my phone and the screen is black but it still vibrates.",
            "Ear speaker is muffled and I can barely hear phone calls.",
            "Camera screen shows purple lines and won't focus."
        ],
        "default_escalate": True,
        "historical_action": "Assess physical/liquid damage and recommend scheduling an appointment at an Apple Authorized Service Provider or Genius Bar."
    },
    "connectivity_network": {
        "name": "Wi-Fi, Bluetooth & Cellular",
        "description": "Unable to connect to Wi-Fi, Bluetooth pairing drops, cellular showing 'No Service', or personal hotspot issues.",
        "examples": [
            "Wi-Fi keeps dropping every 5 minutes on my MacBook.",
            "Phone says 'No Service' even after taking SIM card out.",
            "Bluetooth won't discover my AirPods."
        ],
        "default_escalate": False,
        "historical_action": "Advise toggling Airplane Mode, resetting network settings (Settings > General > Reset > Reset Network Settings), or reseating SIM."
    },
    "app_performance_crash": {
        "name": "App Crashes & System Freeze",
        "description": "Individual apps crashing on launch, keyboard lag, App Store download issues, or UI freezing.",
        "examples": [
            "Messages app crashes whenever I try to send a photo.",
            "Keyboard is lagging heavily when typing.",
            "App Store won't download or update any apps."
        ],
        "default_escalate": False,
        "historical_action": "Recommend force-quitting the app, checking for app updates in the App Store, or performing a forced restart."
    },
    "other_general": {
        "name": "General Inquiries & Feedback",
        "description": "Trade-in inquiries, retail store appointments, warranty questions, feature how-tos, or feedback.",
        "examples": [
            "How much trade-in value do I get for an iPhone 6s?",
            "Can I walk into an Apple Store without an appointment?",
            "When will Apple Pay be available in my country?"
        ],
        "default_escalate": False,
        "historical_action": "Provide official apple.com resource links or guide user to Apple Store reservations."
    }
}
