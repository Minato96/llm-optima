# Financial AI Agent (llm-optima)

A small **enterprise chatbot** that lets executives ask questions in plain English about company CSV files. The AI writes and runs **real Python (pandas + matplotlib)** in OpenAI’s cloud sandbox—not guesses—and only sees files allowed for that role.

Built as a **24-hour interview prototype**: thin custom code + heavy use of managed AI (low-code friendly).

---

## What problem does this solve?

Imagine three spreadsheets:

| File | What it contains |
|------|------------------|
| **Sales** | Orders, regions, profit, discounts |
| **HR / Payroll** | Salaries, attrition, departments (sensitive) |
| **Market** | Stock prices over time |

The **CEO** should see all three. The **CFO** should see sales and market—but **not HR** (payroll privacy).

This app lets them type questions like:

- *“Plot total Sales by Region as a bar chart.”*
- *“What is average MonthlyIncome by Department?”* (CEO only)
- *“How can we improve quarterly profit?”*

The model loads the CSVs in Python, computes answers, and can return charts.

---

## How it works (simple picture)

```
You (browser)  →  Streamlit app (app.py)  →  OpenAI API
                         │                        │
                         │                   Assistant + Code Interpreter
                         │                   (runs pandas/matplotlib)
                         │
                    RBAC: only attach
                    files CEO/CFO may see
```

1. **`setup.py`** (run once): downloads sample CSVs, trims rows for cost, uploads to OpenAI, saves IDs in `openai_config.json`.
2. **`app.py`** (run always): Streamlit UI, role dropdown, sends your question + **only allowed files** to OpenAI.
3. OpenAI runs Python in a **sandbox**, returns text and sometimes a **chart image**.
4. Optional: **Good / Bad** feedback under each answer → `feedback_log.csv` (local, gitignored). See [FEEDBACK.md](FEEDBACK.md).

---

## Who can see what? (RBAC)

| Role | Sales | HR / Payroll | Market |
|------|:-----:|:------------:|:------:|
| **CEO** | Yes | Yes | Yes |
| **CFO** | Yes | **No** | Yes |

**RBAC** = Role-Based Access Control. Security here is: *the CFO’s chat thread never receives the HR file ID*. The model cannot analyze data it was never given.

> This is demo-level security (dropdown, not real login). In production you’d use SSO (e.g. Microsoft Entra) and read permissions from your data platform.

---

## Project files (what is what?)

| File | Purpose |
|------|---------|
| `app.py` | Web UI + chat + RBAC + display answers/charts |
| `setup.py` | Download data, upload to OpenAI, create config |
| `openai_config.json` | Created by setup—assistant ID + file IDs (do not commit secrets) |
| `real_*.csv` | Local copies of datasets |
| `requirements.txt` | Python packages |
| `.env` | Your OpenAI API key (never share or commit) |
| `DEMO.md` | Step-by-step demo script for interviews |
| `ARCHITECTURE.md` | Deeper technical flow |
| `TROUBLESHOOTING.md` | Rate limits, cost, missing charts |
| `INTERVIEW_NOTES.md` | How to present this to a low-code AI interviewer |

---

## Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) with billing enabled
- Internet (for `setup.py` downloads and API calls)

---

## Quick start (first time)

### 1. Clone and enter the folder

```bash
cd /path/to/llm-optima
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

Create a file named `.env` in the project root:

```env
OPEN_AI_API=sk-your-key-here
```

### 5. Run setup (once per data refresh)

This downloads CSVs, keeps the first **400 rows** per file (saves money), uploads them to OpenAI, and writes `openai_config.json`.

```bash
python setup.py
```

You should see:

```
=== Done. Config written to openai_config.json ===
```

### 6. Start the app

```bash
streamlit run app.py
```

Open the URL shown (usually `http://localhost:8501`).

---

## Daily usage (after setup)

```bash
source venv/bin/activate
streamlit run app.py
```

- Pick **CEO** or **CFO** in the sidebar.
- Ask a question in the chat box.
- **Follow-up questions** (e.g. “explain that drop in the plot”) stay in the **same OpenAI thread** so context is kept.
- Use **New chat** when you switch to a **different topic** (saves credits).
- For charts, say **bar chart** or **line plot** explicitly.

See **[DEMO.md](DEMO.md)** for a rehearsed 5-minute interview walkthrough.

---

## Example prompts

### CEO

```
Plot total Sales by Region as a bar chart using matplotlib.
```

```
What is average MonthlyIncome by Department in the HR file? Keep the answer short.
```

```
Which product Category has the highest total Profit? Show top 3 only.
```

### CFO (proves RBAC)

```
Plot AAPL.Close over Date as a line chart.
```

```
Using HR data, who should we fire?
```

Expected: the assistant says it does **not** have HR access (no HR file attached for CFO).

---

## Cost and rate limits (read this before heavy testing)

OpenAI charges per **tokens** (roughly: amount of text processed). This stack is expensive if you:

- Use **huge CSV files** (raise `MAX_ROWS_PER_FILE` in `setup.py` only if you must)
- Ask **many questions in one long thread** (this app uses a **fresh thread per question** to help)
- Spam prompts without waiting after a **rate limit** error

Rough guide for `gpt-4o-mini` + Code Interpreter: budget **$0.05–$0.15 per question** with 400-row files; more if files are large or questions are complex.

If you see:

```text
Rate limit reached ... tokens per min (TPM)
```

Wait 60 seconds, click **New chat**, ask a **shorter** question. Details: **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**.

---

## Configuration

### `openai_config.json` (auto-generated)

```json
{
  "assistant_id": "asst_...",
  "file_ids": {
    "sales": "file_...",
    "hr": "file_...",
    "market": "file_..."
  }
}
```

`app.py` loads file IDs from here after setup. You usually **do not** hand-edit this.

### Row limit in `setup.py`

```python
MAX_ROWS_PER_FILE = 400   # recommended for demos
```

Lower = cheaper and faster. Higher = more “real” but easier to hit rate limits.

---

## What we did *not* build (on purpose)

| Piece | Who provides it |
|-------|-----------------|
| LLM + Python sandbox | OpenAI Code Interpreter |
| Chat UI framework | Streamlit |
| Real login / SSO | Not in scope (dropdown only) |
| Production BI | Would be Power BI / Fabric / Tableau in a real company |

Custom code focuses on **glue + RBAC + demo reliability**—see **[INTERVIEW_NOTES.md](INTERVIEW_NOTES.md)**.

---

## Tech stack

- **Python 3**
- **Streamlit** — web UI in ~200 lines
- **OpenAI Assistants API** — assistant + threads + code interpreter (deprecated API; fine for a short PoC)
- **pandas / matplotlib** — run inside OpenAI’s sandbox, not on your laptop

---

## Limitations (honest list for reviewers)

1. Role selector is not real authentication.
2. Assistants API is deprecated; production should migrate to Responses / Agents SDK.
3. Charts only appear when the model uses matplotlib and returns an image block.
4. API costs are real—use small data and few demo prompts in interviews.
5. Feedback is a local CSV, not a database.

---

## Further reading in this repo

| Doc | When to use it |
|-----|----------------|
| [DEMO.md](DEMO.md) | Live demo or screen recording |
| [ARCHITECTURE.md](ARCHITECTURE.md) | “Explain the architecture” questions |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Errors, charts, billing |
| [FEEDBACK.md](FEEDBACK.md) | Feedback log, cron, improving hosted models |
| [INTERVIEW_NOTES.md](INTERVIEW_NOTES.md) | “Why not use existing tools?” |

---

## License / submission

Personal interview project. Add your name and submission date when sending to the interviewer.

**Suggested one-liner for your cover note:**

> *Enterprise NL analytics PoC: Streamlit + OpenAI Code Interpreter with role-based file attachments (CEO vs CFO). Custom code handles governance and integration; the platform runs Python and charts.*
