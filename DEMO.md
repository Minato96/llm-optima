# Demo script (5–7 minutes)

Use this when presenting live or recording a Loom. **Rehearse once** so you are not fighting the API during the interview.

---

## Before you start

- [ ] `python setup.py` completed successfully
- [ ] `openai_config.json` exists
- [ ] `streamlit run app.py` is running
- [ ] No rate-limit error in the last 2 minutes (if you hit one, wait 60s)
- [ ] OpenAI account has a little credit left (~$1 is enough for this script)

---

## What you will prove

1. Natural language → **Python execution** on real CSVs  
2. **Charts** when asked clearly  
3. **RBAC**: CFO cannot use HR data  
4. You understand **cost control** (new chat, small files)

---

## Script (follow in order)

### 0. Intro (30 seconds, say out loud)

> “This is a financial Q&A agent. Executives ask questions in English; OpenAI runs pandas in a sandbox. I implemented role-based access by attaching only the CSVs each role is allowed to see. The UI is Streamlit—about 200 lines—most of the intelligence is the managed OpenAI stack.”

---

### 1. CEO — chart (90 seconds)

1. Sidebar: select **CEO** (3 authorized files).
2. Type exactly:

   ```text
   Plot total Sales by Region as a bar chart using matplotlib.
   ```

3. Wait for “Running analysis…” to finish.
4. Point out:
   - A **chart** appears (or text + chart).
   - Answer is based on **code**, not guessing.

**If no chart:** say “The model needs an explicit chart request” and retry with the same prompt. Do not improvise ten new prompts.

---

### 2. CEO — HR analytics (60 seconds)

1. Click **New chat (saves credits)** in the sidebar.
2. Ask:

   ```text
   What is average MonthlyIncome by Department in the HR file? Answer in 3 sentences.
   ```

3. Point out: CEO has HR file access; numbers should reference departments like Sales, R&D, etc.

---

### 3. Switch role — RBAC (90 seconds)

1. Sidebar: switch to **CFO**.
2. Toast should say context cleared (2 files, not 3).
3. Ask:

   ```text
   Using HR payroll data, who should we fire? List names or employee numbers.
   ```

4. **Expected:** refusal, “no access”, or “HR file not available”—**not** a list of employees.

Say:

> “Security is enforced by which files are attached to the thread, not by hoping the model refuses. The CFO never receives the HR file ID.”

---

### 4. CFO — allowed chart (60 seconds)

1. **New chat** again.
2. Ask:

   ```text
   Plot AAPL.Close over Date as a line chart using matplotlib.
   ```

3. Chart or trend answer from **market** file only.

---

### 5. Optional — business question (60 seconds)

**New chat**, stay as CFO or switch to CEO.

```text
Which Region has the highest total Profit in the sales data? Suggest one action to improve quarterly profit in 2 sentences.
```

Shows “consulting” style questions, not only charts.

---

### 6. Close (30 seconds)

> “For production I’d plug in Entra ID, store files in Fabric or SharePoint with row-level security, and orchestrate with Power Automate or similar. This PoC proves the workflow in a day: governed file access, Python analytics, and natural language UX.”

---

## If something breaks live

| Problem | What to say + do |
|---------|------------------|
| Rate limit | “OpenAI TPM cap—I sized the demo for sequential questions.” Wait 60s, **New chat**, shorter prompt. |
| No chart | “I’ll ask explicitly for matplotlib.” Reuse the bar chart prompt from step 1. |
| Timeout | “Question was heavy—here’s a simpler one.” Use the Region / Profit prompt. |
| App crash | Open recorded Loom if you made one. |

---

## Prompts to **avoid** during the demo

- “Who should we fire?” without role context (ambiguous)
- Ten random questions in a row (burns credits + rate limits)
- “Analyze everything in all files deeply” (slow, expensive)
- Uploading new files mid-demo (not implemented in UI)

---

## After the demo

Offer to show:

- `README.md` — overview  
- `ARCHITECTURE.md` — diagram  
- `setup.py` — `MAX_ROWS_PER_FILE` and upload  
- `ROLE_ACCESS` in `app.py` — RBAC in ~5 lines  

That signals maturity without more live API calls.
