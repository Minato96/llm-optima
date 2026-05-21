# llm-optima — Financial AI Agent

Natural-language Q&A over enterprise CSV data. Users ask questions in plain English; **OpenAI Code Interpreter** runs **pandas** and **matplotlib** in a managed sandbox. Access to datasets is enforced by **role** (CEO vs CFO) before any analysis runs.

---

## Features

- Chat UI for financial and workforce questions
- Python-backed answers (computed, not guessed)
- Charts when requested (matplotlib in sandbox)
- **Role-based access:** CEO — 3 files; CFO — 2 files (no HR/payroll)
- Follow-up questions in the same conversation thread
- Charts stay visible in the UI after later messages
- Structured feedback (Good / Bad + reason) → local CSV log

---

## How it works

```
Browser (Streamlit)
       │
       ▼
  app.py — role check, chat UI, feedback
       │
       ▼
  OpenAI API
       ├── Assistant (instructions + gpt-4o-mini)
       ├── Thread (conversation + file attachments)
       └── Code Interpreter (pandas / matplotlib on CSVs)
```

1. **`setup.py`** (once): download sample CSVs, trim rows, upload to OpenAI, write `openai_config.json`.
2. **`app.py`**: user picks role, asks a question; only allowed files attach to the thread.
3. OpenAI runs generated Python; the app shows text and any chart image.
4. Optional feedback is appended to `feedback_log.csv` (gitignored).

---

## Requirements

- Python 3.10+
- OpenAI API key with billing enabled
- Internet (dataset download + API)

---

## Setup

```bash
git clone https://github.com/Minato96/llm-optima.git
cd llm-optima
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in the project root:

```env
OPEN_AI_API=sk-your-key-here
```

Run setup (downloads data, uploads files, creates assistant config):

```bash
python setup.py
```

Start the application:

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

---

## Usage

### Roles

| Role | Sales | HR / payroll | Market data |
|------|:-----:|:------------:|:-----------:|
| CEO  | ✓ | ✓ | ✓ |
| CFO  | ✓ | ✗ | ✓ |

The CFO thread never receives the HR file. Enforcement is at **file attachment**, not only in the system prompt.

### Example questions

**CEO**

- `Plot total Sales by Region as a bar chart using matplotlib.`
- `What is average MonthlyIncome by Department in the HR file?`
- `Which Region has the highest total Profit?`

**CFO**

- `Plot AAPL.Close over Date as a line chart.`
- `Using HR data, who should we fire?` → expect no access to HR data

### Tips

- Mention **bar chart** or **line plot** when you need a visualization.
- **Follow-up** questions (e.g. “explain that drop”) use the same OpenAI thread and keep context.
- Click **New chat** when switching to a **different topic** to limit API cost.
- After ~8 turns in one thread, start a new chat for heavy topics.

---

## Configuration

| Item | Location | Purpose |
|------|----------|---------|
| API key | `.env` → `OPEN_AI_API` | OpenAI authentication |
| Assistant & file IDs | `openai_config.json` | Written by `setup.py`; reused by `app.py` |
| Row limit | `setup.py` → `MAX_ROWS_PER_FILE` | Default `400`; lower = cheaper, higher = slower/costlier |

Re-run `python setup.py` after changing data or if file IDs expire.

---

## Feedback

Under each assistant reply: **Good** or **Bad** (with reason categories).

Logs are written to **`feedback_log.csv`** in the project root (gitignored). The sidebar shows the path and entry count.

| Column | Description |
|--------|-------------|
| `timestamp_utc` | When feedback was submitted |
| `role` | CEO / CFO |
| `user_prompt` | User question |
| `assistant_response` | Answer text (truncated at 8k chars) |
| `rating` | `good` / `bad` |
| `reason_category` | Selected reason for bad feedback |
| `reason_detail` | Free text (e.g. “Other”) |
| `thread_id` | OpenAI thread ID |
| `has_chart` | Whether the reply included a chart |

Example schema: `feedback_log.csv.example`.

In production, this would move to a database and feed human review or evaluation pipelines—not automatic model retraining.

---

## Cost and rate limits

- Billing is per OpenAI usage (tokens + Code Interpreter). With trimmed CSVs, expect roughly **$0.05–$0.15 per question**; complex or long threads cost more.
- If you hit **TPM rate limits**, wait ~60 seconds, click **New chat**, and use a shorter prompt.
- Avoid many unrelated questions in one long thread without starting fresh.

---

## Project layout

```
llm-optima/
├── app.py                 # Streamlit UI and OpenAI integration
├── setup.py               # Data download, upload, config generation
├── feedback.py            # Feedback CSV logging
├── requirements.txt
├── openai_config.json     # Generated; not committed
├── openai_config.json.example
├── feedback_log.csv       # Generated; not committed
├── real_sales_data.csv    # Local datasets
├── real_hr_payroll_data.csv
├── real_market_data.csv
└── docs/
    └── architecture.md    # Technical design
```

---

## Stack

| Layer | Technology |
|-------|------------|
| UI | Streamlit |
| LLM + sandbox | OpenAI Assistants API, Code Interpreter, `gpt-4o-mini` |
| Data prep | pandas, numpy |
| Config | python-dotenv |

---

## Limitations (current PoC)

- Role selector is a demo control, not SSO.
- Assistants API is deprecated; plan migration to Responses / Agents SDK for long-term use.
- Charts depend on the model following matplotlib instructions.
- Analytics run in OpenAI’s cloud, not on-premises.
- Feedback is a local CSV only.

See [docs/architecture.md](docs/architecture.md) for design detail and production direction.

---

## License

See repository owner for usage terms.
