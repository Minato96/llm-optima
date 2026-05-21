import base64
import json
import re
import time
import warnings
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from feedback import (
    BAD_REASONS,
    FEEDBACK_PATH,
    assistant_text,
    count_feedback_rows,
    ensure_feedback_log,
    log_feedback,
    user_prompt_for_turn,
)

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*The Assistants API is deprecated.*",
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_API"))

CONFIG_PATH = Path("openai_config.json")

# Paste IDs from setup.py, or load from openai_config.json after running setup.
SALES_FILE_ID = "file-Qc4pHTCqTvf1oQchFzBtrW"
HR_PAYROLL_FILE_ID = "file-7QaDqMUzxmaqPWVTgwh5WP"
MARKET_FILE_ID = "file-QUpyd5QQ4mAQpqPgtQwqjr"

ROLE_ACCESS = {
    "CEO": [SALES_FILE_ID, HR_PAYROLL_FILE_ID, MARKET_FILE_ID],
    "CFO": [SALES_FILE_ID, MARKET_FILE_ID],
}

ASSISTANT_INSTRUCTIONS = """You are an enterprise financial analyst with access to CSV files in a Python sandbox.

Rules:
1. Always load data with pandas and compute answers in Python—never guess numbers.
2. Keep final text answers short (under 8 sentences) unless the user asks for detail.
3. When the user asks for a chart, plot, graph, trend, or visualization:
   - Use matplotlib only (import matplotlib.pyplot as plt).
   - Create one clear chart, plt.tight_layout(), then plt.show() so the figure is returned.
   - Do not only describe the chart in text—always render it.
4. Use small samples (e.g. df.head(200)) when exploring; only process full files when needed.
5. CFO may not have HR data—if a question needs HR and you lack that file, say access is denied.
6. Use the full conversation history. If the user refers to "the plot", "that drop", or a prior answer, continue that analysis—do not ask which files to use unless the topic truly changed.
"""

MAX_RUN_SECONDS = 120
POLL_INTERVAL_SEC = 2
# Follow-ups in the same thread see prior Q&A. Click "New chat" between unrelated topics.
MAX_TURNS_PER_THREAD = 8


def load_config():
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(data):
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@st.cache_resource
def get_assistant_id():
    """Reuse one assistant across restarts — avoids duplicate assistants and extra setup cost."""
    cfg = load_config()
    if cfg.get("assistant_id"):
        return cfg["assistant_id"]

    assistant = client.beta.assistants.create(
        name="Enterprise Financial AI",
        instructions=ASSISTANT_INSTRUCTIONS,
        model="gpt-4o-mini",
        tools=[{"type": "code_interpreter"}],
    )
    cfg["assistant_id"] = assistant.id
    file_ids = cfg.get("file_ids", {})
    file_ids.update(
        {
            "sales": SALES_FILE_ID,
            "hr": HR_PAYROLL_FILE_ID,
            "market": MARKET_FILE_ID,
        }
    )
    cfg["file_ids"] = file_ids
    save_config(cfg)
    return assistant.id


def parse_retry_seconds(error_message: str) -> float:
    match = re.search(r"try again in ([\d.]+)s", error_message or "", re.I)
    if match:
        return float(match.group(1)) + 0.5
    return 5.0


def wait_for_run(thread_id: str, run_id: str, status_placeholder):
    deadline = time.time() + MAX_RUN_SECONDS
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

    while run.status in ("queued", "in_progress"):
        if time.time() > deadline:
            raise TimeoutError("Run timed out after 2 minutes. Try a simpler question or New chat.")
        status_placeholder.text(f"Running analysis ({run.status})…")
        time.sleep(POLL_INTERVAL_SEC)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

    return run


def create_run_with_retry(thread_id: str, assistant_id: str, status_placeholder, max_retries=5):
    for attempt in range(max_retries):
        try:
            return client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )
        except Exception as exc:
            msg = str(exc)
            if "rate_limit" in msg.lower() or "429" in msg:
                wait = parse_retry_seconds(msg) * (attempt + 1)
                status_placeholder.warning(
                    f"Rate limit hit — waiting {wait:.0f}s before retry ({attempt + 1}/{max_retries})…"
                )
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Rate limit persists. Wait 60s, click New chat, and ask a shorter question.")


def create_thread_with_files(role: str, prompt: str):
    attachments = [
        {"file_id": fid, "tools": [{"type": "code_interpreter"}]}
        for fid in ROLE_ACCESS[role]
    ]
    return client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
                "attachments": attachments,
            }
        ]
    )


def add_user_message_to_thread(thread_id: str, prompt: str):
    return client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt,
    )


def fetch_image_bytes(image_file_id: str) -> bytes:
    return client.files.content(image_file_id).read()


def render_message(msg: dict):
    """Render one stored chat message (user text or assistant parts with persisted charts)."""
    if msg["role"] == "user":
        st.markdown(msg["content"])
        return

    if "parts" not in msg:
        # Older sessions stored a placeholder instead of image bytes.
        content = msg.get("content", "")
        if content.startswith("![chart]"):
            st.caption("Chart from an earlier session — re-ask with “plot” to regenerate.")
        else:
            st.markdown(content)
        return

    for part in msg.get("parts", []):
        if part["type"] == "image":
            st.image(base64.b64decode(part["data"]))
        elif part["type"] == "text":
            st.markdown(part["content"])


def render_assistant_message(
    message,
    session_messages: list,
    *,
    role: str,
    user_prompt: str,
    thread_id: str,
):
    """Show text and chart blocks; persist image bytes so charts survive the next prompt."""
    parts = []

    for block in message.content:
        if block.type == "image_file":
            image_bytes = fetch_image_bytes(block.image_file.file_id)
            parts.append(
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            )
        elif block.type == "text":
            parts.append({"type": "text", "content": block.text.value})

    if not parts:
        return

    stored = {
        "role": "assistant",
        "parts": parts,
        "meta": {
            "role": role,
            "user_prompt": user_prompt,
            "thread_id": thread_id,
            "has_chart": any(p["type"] == "image" for p in parts),
        },
        "feedback": None,
    }
    session_messages.append(stored)

    for part in parts:
        if part["type"] == "image":
            st.image(base64.b64decode(part["data"]))
        else:
            st.markdown(part["content"])


def record_feedback(message_index: int, rating: str, reason: str = "", detail: str = ""):
    msg = st.session_state.messages[message_index]
    meta = msg.get("meta", {})
    log_feedback(
        role=meta.get("role", st.session_state.get("current_role", "")),
        user_prompt=meta.get("user_prompt") or user_prompt_for_turn(
            st.session_state.messages, message_index
        ),
        assistant_response=assistant_text(msg),
        rating=rating,
        reason_category=reason,
        reason_detail=detail,
        thread_id=meta.get("thread_id", st.session_state.get("thread_id", "")),
        has_chart=meta.get("has_chart", False),
    )
    msg["feedback"] = {
        "rating": rating,
        "reason": reason,
        "detail": detail,
    }


def render_feedback_ui(message_index: int):
    msg = st.session_state.messages[message_index]
    if msg.get("feedback"):
        fb = msg["feedback"]
        label = fb["rating"]
        if fb.get("reason"):
            label += f" — {fb['reason']}"
        st.caption(f"Feedback recorded ({label})")
        return

    st.caption("Was this helpful?")
    col1, col2 = st.columns(2)
    if col1.button("Good", key=f"fb_good_{message_index}"):
        record_feedback(message_index, "good")
        st.toast(f"Saved to {FEEDBACK_PATH}")
        st.rerun()

    if col2.button("Bad", key=f"fb_bad_{message_index}"):
        st.session_state.feedback_bad_idx = message_index
        st.rerun()

    if st.session_state.get("feedback_bad_idx") == message_index:
        reason = st.selectbox(
            "What went wrong?",
            BAD_REASONS,
            key=f"fb_reason_{message_index}",
        )
        detail = ""
        if reason == "Other":
            detail = st.text_input(
                "Describe the issue",
                key=f"fb_detail_{message_index}",
            )
        if st.button("Submit feedback", key=f"fb_submit_{message_index}"):
            record_feedback(message_index, "bad", reason, detail)
            st.session_state.feedback_bad_idx = None
            st.toast(f"Saved to {FEEDBACK_PATH}")
            st.rerun()


def last_assistant_index_without_feedback() -> int | None:
    pending = None
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant" and not msg.get("feedback"):
            pending = idx
    return pending


assistant_id = get_assistant_id()
cfg = load_config()
if cfg.get("file_ids"):
    ROLE_ACCESS["CEO"] = [
        cfg["file_ids"].get("sales", SALES_FILE_ID),
        cfg["file_ids"].get("hr", HR_PAYROLL_FILE_ID),
        cfg["file_ids"].get("market", MARKET_FILE_ID),
    ]
    ROLE_ACCESS["CFO"] = [
        cfg["file_ids"].get("sales", SALES_FILE_ID),
        cfg["file_ids"].get("market", MARKET_FILE_ID),
    ]

st.set_page_config(page_title="Financial AI Agent", layout="wide")
st.title("Financial AI Agent")
st.markdown(
    "Ask questions about enterprise CSVs. Python runs in OpenAI's sandbox. "
    "**Tip:** ask explicitly for a *bar chart* or *line plot* to get visuals."
)

role = st.sidebar.selectbox("Log in as:", ["CEO", "CFO"])
st.sidebar.markdown(f"**Authorized files:** {len(ROLE_ACCESS[role])}")

if st.sidebar.button("New chat"):
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.thread_turns = 0
    st.rerun()

st.sidebar.caption(
    "Follow-up questions keep context in one OpenAI thread. "
    "Click **New chat** when you switch topics (saves credits). "
    f"Auto-hint after {MAX_TURNS_PER_THREAD} turns in one thread."
)

ensure_feedback_log()
st.sidebar.markdown("---")
st.sidebar.markdown("**Feedback log**")
st.sidebar.code(str(FEEDBACK_PATH.resolve()), language=None)
st.sidebar.caption(f"{count_feedback_rows()} row(s) in feedback_log.csv (gitignored).")

if "current_role" not in st.session_state or st.session_state.current_role != role:
    st.session_state.current_role = role
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.thread_turns = 0
    st.toast(f"Switched to {role}. Chat cleared.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "thread_turns" not in st.session_state:
    st.session_state.thread_turns = 0
if "feedback_bad_idx" not in st.session_state:
    st.session_state.feedback_bad_idx = None

feedback_idx = last_assistant_index_without_feedback()

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        render_message(msg)
        if idx == feedback_idx:
            render_feedback_ui(idx)

if prompt := st.chat_input("e.g. Plot quarterly profit by region as a bar chart"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_text = st.empty()
        try:
            thread_id = st.session_state.thread_id

            if thread_id is None:
                status_text.text("Starting secure session with your authorized files…")
                thread = create_thread_with_files(role, prompt)
                thread_id = thread.id
                st.session_state.thread_id = thread_id
                st.session_state.thread_turns = 1
            else:
                turns = st.session_state.get("thread_turns", 0)
                if turns >= MAX_TURNS_PER_THREAD:
                    st.sidebar.warning(
                        f"{MAX_TURNS_PER_THREAD} turns in this thread — use **New chat** soon to limit cost."
                    )
                status_text.text("Continuing conversation (prior messages included)…")
                add_user_message_to_thread(thread_id, prompt)
                st.session_state.thread_turns = turns + 1

            run = create_run_with_retry(thread_id, assistant_id, status_text)
            run = wait_for_run(thread_id, run.id, status_text)

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                latest = messages.data[0]
                status_text.empty()
                render_assistant_message(
                    latest,
                    st.session_state.messages,
                    role=role,
                    user_prompt=prompt,
                    thread_id=thread_id,
                )
                render_feedback_ui(len(st.session_state.messages) - 1)
            elif run.status == "failed":
                error_msg = run.last_error.message if run.last_error else "Unknown error"
                status_text.error(f"Run failed: {error_msg}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error: {error_msg}"}
                )
            else:
                status_text.warning(f"Run ended with status: {run.status}")
        except Exception as exc:
            status_text.error(str(exc))
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {exc}"})
