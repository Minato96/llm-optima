import base64
import csv
import json
import re
import time
import warnings
from pathlib import Path
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

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
"""

MAX_RUN_SECONDS = 120
POLL_INTERVAL_SEC = 2


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


def render_assistant_message(message, session_messages: list):
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

    session_messages.append({"role": "assistant", "parts": parts})

    for part in parts:
        if part["type"] == "image":
            st.image(base64.b64decode(part["data"]))
        else:
            st.markdown(part["content"])


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

if st.sidebar.button("New chat (saves credits)"):
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.rerun()

st.sidebar.caption(
    "Cost tips: one topic per chat, use New chat between unrelated questions, "
    "and keep prompts specific. Large thread history causes rate limits."
)

if "current_role" not in st.session_state or st.session_state.current_role != role:
    st.session_state.current_role = role
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.toast(f"Switched to {role}. Chat cleared.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render_message(msg)

if prompt := st.chat_input("e.g. Plot quarterly profit by region as a bar chart"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_text = st.empty()
        try:
            # Fresh thread per question = far fewer tokens than one long thread.
            status_text.text("Starting secure session with your authorized files…")
            thread = create_thread_with_files(role, prompt)
            st.session_state.thread_id = thread.id

            run = create_run_with_retry(thread.id, assistant_id, status_text)
            run = wait_for_run(thread.id, run.id, status_text)

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                latest = messages.data[0]
                status_text.empty()
                render_assistant_message(latest, st.session_state.messages)

                st.markdown("---")
                c1, c2 = st.columns([1, 4])
                with c1:
                    if st.button("Good", key=f"up_{time.time()}"):
                        with open("feedback_log.csv", "a", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow([role, prompt, "Good"])
                        st.toast("Feedback saved.")
                with c2:
                    if st.button("Bad", key=f"down_{time.time()}"):
                        with open("feedback_log.csv", "a", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerow([role, prompt, "Bad"])
                        st.toast("Feedback saved.")
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
