"""Append-only feedback log for human review and future ML pipelines."""

import csv
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_PATH = Path("feedback_log.csv")

FIELDNAMES = [
    "timestamp_utc",
    "role",
    "user_prompt",
    "assistant_response",
    "rating",
    "reason_category",
    "reason_detail",
    "thread_id",
    "has_chart",
]

BAD_REASONS = [
    "Wrong numbers or facts",
    "Did not follow my question",
    "Missing or bad chart",
    "Too long / too vague",
    "Security or access issue",
    "Other",
]


def ensure_feedback_log() -> None:
    if FEEDBACK_PATH.exists():
        return
    with FEEDBACK_PATH.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def count_feedback_rows() -> int:
    ensure_feedback_log()
    with FEEDBACK_PATH.open(encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


def assistant_text(message: dict) -> str:
    if "parts" in message:
        chunks = [p["content"] for p in message["parts"] if p["type"] == "text"]
        return "\n\n".join(chunks).strip()
    return (message.get("content") or "").strip()


def user_prompt_for_turn(messages: list, assistant_index: int) -> str:
    for i in range(assistant_index - 1, -1, -1):
        if messages[i]["role"] == "user":
            return messages[i]["content"]
    return messages[assistant_index].get("meta", {}).get("user_prompt", "")


def log_feedback(
    *,
    role: str,
    user_prompt: str,
    assistant_response: str,
    rating: str,
    reason_category: str = "",
    reason_detail: str = "",
    thread_id: str = "",
    has_chart: bool = False,
) -> None:
    ensure_feedback_log()
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "user_prompt": user_prompt,
        "assistant_response": assistant_response[:8000],
        "rating": rating,
        "reason_category": reason_category,
        "reason_detail": reason_detail,
        "thread_id": thread_id,
        "has_chart": str(has_chart),
    }
    with FEEDBACK_PATH.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)
