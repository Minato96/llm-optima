# Feedback system

How feedback works in this PoC, where it is stored, and how you would use it in production—including when the “model” is OpenAI and you do not train it yourself.

---

## Is the PoC feedback “good enough”?

| For… | Verdict |
|------|---------|
| **PoC / stakeholder demo** | Yes, after the fix: proves human-in-the-loop review was considered |
| **Production** | No — needs DB, auth, PII rules, and a defined ML/ops pipeline |

---

## Why it felt broken before

The old **Good / Bad** buttons lived **inside** the `chat_input` handler. On click, Streamlit reruns the app; the new prompt is empty, so that whole block was skipped and **nothing was written**.

**Now:** buttons render under the **last assistant reply** in the main chat loop, so they survive reruns and append to `feedback_log.csv`.

---

## How to use it (today)

1. Run the app and get an assistant answer.
2. Under that answer, click **Good** or **Bad**.
3. For **Bad**, pick a reason (or **Other** + text) → **Submit feedback**.
4. Sidebar shows the log path and row count.
5. Open the file on disk:

   ```bash
   cat feedback_log.csv
   ```

   Path is the project root, e.g. `/home/charan/projects/llm-optima/feedback_log.csv`.

The file is in **`.gitignore`** (so you will not see it on GitHub—only locally). That is intentional for prompts/responses.

### CSV columns

| Column | Meaning |
|--------|---------|
| `timestamp_utc` | When feedback was submitted |
| `role` | CEO / CFO |
| `user_prompt` | User question for that turn |
| `assistant_response` | Text of the answer (truncated at 8k chars) |
| `rating` | `good` or `bad` |
| `reason_category` | Dropdown (bad only) |
| `reason_detail` | Free text (especially for Other) |
| `thread_id` | OpenAI thread (for support/debug) |
| `has_chart` | `True` / `False` |

---

## Daily / monthly cron — what to run

Cron does **not** call OpenAI. It only **collects and processes** `feedback_log.csv` (or copies from a DB in production).

Example monthly job:

```bash
# 1) Archive this month's file
cp feedback_log.csv "archive/feedback_$(date +%Y-%m).csv"

# 2) Build a review report (example: count bad by reason)
python scripts/feedback_report.py

# 3) Optional: upload bad rows to a ticket queue / Slack / email
```

A minimal `feedback_report.py` would:

- Filter `rating == bad`
- Group by `reason_category`
- Output top prompts for human review

**Humans** fix: prompts, instructions, data, RBAC—not the cron itself.

---

## “Train the model” when using OpenAI — what actually works

You **do not** retrain GPT weights on your laptop. Options:

### 1. Human review loop (start here — PoC → prod)

```
User bad feedback → CSV/DB → analyst reviews weekly
    → update assistant instructions / prompts / data
    → redeploy
```

Cheap, explainable, what most enterprises do first.

### 2. Evaluation set (recommended before any “training”)

- Turn each bad row into a **test case**: prompt + expected properties (e.g. “must mention no HR access”).
- Run nightly against new prompt versions.
- This is **not** training; it is **quality gates**.

### 3. OpenAI fine-tuning (optional, later)

- Export JSONL: `{"messages": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}` from **good** examples and corrected bad examples (human-written fixes).
- Use [OpenAI fine-tuning](https://platform.openai.com/docs/guides/fine-tuning) on `gpt-4o-mini` (or a supported model).
- **Tradeoff:** cost + maintenance; only worth it with hundreds/thousands of curated pairs and stable task format.

You are still calling **their** hosted model—just a customized version.

### 4. RAG / context injection (often better than fine-tuning)

For bad answers “wrong numbers” / “ignored file”:

- Store feedback + thread_id + snippet of context in a vector DB or table.
- On similar new questions, inject: “Previous mistake: …; rule: always use pandas on attached file.”

No weight training; improves behavior faster for analytics chatbots.

### 5. Tool routing (production pattern)

Don’t let the model freestyle pandas every time:

- `run_sql`, `plot_metric`, `list_allowed_tables` as **fixed tools**
- Bad feedback → disable free-form code path for that metric

### 6. What you usually **cannot** do

- Train GPT-4o inside your repo on a cron schedule  
- Automatically “learn” from bad clicks without human labels or curated corrections  
- Send full enterprise CSV context to a training pipeline without privacy review  

---

## Collecting “part of context” safely

If you add more context to feedback later:

| Include | Skip (PII / cost) |
|---------|-------------------|
| `thread_id`, role, file IDs | Full HR rows |
| Last 2k chars of assistant text | Entire CSV |
| Reason category | API keys |
| Hashed user id (prod) | Raw employee names |

OpenAI may already retain thread data per their policy—your log should stay **minimal**.

---

## Production upgrade path

| PoC (`feedback_log.csv`) | Production |
|--------------------------|------------|
| Local CSV | Postgres / Blob + audit |
| No auth | User id from SSO |
| Good/Bad on last message only | Feedback on any turn |
| Manual `cat` | Dashboard + weekly report cron |
| Hope to “train” | Eval suite + prompt versioning + optional fine-tune |

---

## Stakeholder one-liner

> “Feedback is an append-only audit log for human review and evaluation datasets—not automatic retraining. With a hosted model we improve instructions, tools, and governance; fine-tuning or RAG is a later step once we have labeled volume and legal sign-off.”

That framing works for product, compliance, and engineering audiences alike.
