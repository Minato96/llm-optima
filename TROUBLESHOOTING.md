# Troubleshooting

Common problems when running the Financial AI Agent, with plain-language fixes.

---

## Rate limit: tokens per minute (TPM)

### What you see

```text
Rate limit reached for gpt-4o-mini ... Limit 200000, Used 200000 ...
Please try again in 1.377s.
```

### What it means

OpenAI limits how much text your organization can process **per minute**. You sent too much in a short window—usually from:

- Many questions in a row  
- Large CSV files in the sandbox  
- Long previous code outputs (if you used one thread for many questions—older versions did this)

### What to do

1. **Wait** the suggested seconds (or 60 seconds to be safe).  
2. Click **New chat (saves credits)** in the sidebar.  
3. Ask a **shorter, specific** question.  
4. Re-run `python setup.py` if your CSVs are huge—check `MAX_ROWS_PER_FILE = 400` in `setup.py`.  
5. Pause testing for 2–3 minutes between batches.

The app already **retries** rate limits automatically a few times.

---

## Follow-up questions ignore earlier messages ("which file?", "see the plot")

### Cause

This is **not** a weak model. The UI showed old messages, but an older version sent **each question on a brand-new OpenAI thread** with no history. The API only saw your latest sentence.

### Fix (current app)

- First question in a session: new thread + file attachments (RBAC).
- Follow-ups: **same thread** until you click **New chat**.
- Charts stay in the Streamlit UI; the model also sees prior text in the thread.

### Cost tradeoff

| Pattern | Context | Cost |
|---------|---------|------|
| New chat per topic | None across topics | Lowest |
| Same thread for follow-ups | Yes | Grows with each turn |

After ~8 turns, start a **New chat** for a new subject.

---

## Burning through credits quickly

### Symptoms

- ~$1 spent in under 15 prompts  
- OpenAI usage dashboard spikes

### Causes

| Cause | Fix |
|-------|-----|
| Full 10k-row sales file | Set `MAX_ROWS_PER_FILE = 400`, re-run `setup.py` |
| CEO attaches 3 large files every question | Expected; use fewer demo prompts |
| Complex questions (many code loops) | Ask for “top 5 only” or “one chart” |
| Testing 30+ times in an hour | Use [DEMO.md](DEMO.md) script only |

### Cost-saving habits

- One **topic** per session; **New chat** for new topic  
- Demo with **4–5 scripted prompts**, not random exploration  
- Use `gpt-4o-mini` (already set)—do not switch to `gpt-4o` for this PoC  

---

## Charts / visualizations not showing

### Symptoms

- Only text answer, no image  
- Placeholder “Chart was generated in the previous turn” on reload

### Fixes

1. **Ask explicitly:**

   ```text
   Plot total Sales by Region as a bar chart using matplotlib.
   ```

2. Words that help: `chart`, `plot`, `bar chart`, `line chart`, `matplotlib`.

3. Avoid “describe a chart” without “plot” or “draw”.

4. Charts are saved in session memory— they stay visible when you send the next prompt (if an old session still shows “re-run to regenerate”, refresh the app once after updating `app.py`).

### If still no image

- Model may have failed silently—check for error text in red.  
- Try CEO role with only sales file question first (simplest).  
- See OpenAI status page if API is degraded.

---

## `setup.py` fails

### “No module named …”

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Download URL fails

Setup falls back to **synthetic small CSVs**. Demo still works; mention “offline fallback data” in the interview.

### `AuthenticationError` / 401

- Check `.env` has `OPEN_AI_API=sk-...` (no quotes, no spaces).  
- Key must be valid and funded.

### Upload fails

- Network firewall blocking OpenAI  
- File too large—lower `MAX_ROWS_PER_FILE`

---

## `openai_config.json` missing

Run:

```bash
python setup.py
```

Then start Streamlit again. `app.py` can fall back to hardcoded file IDs in the source, but those IDs **expire** on OpenAI’s side—always prefer fresh setup.

---

## Assistant / file ID invalid

### Symptoms

```text
No such file object: file-...
```

### Fix

1. `python setup.py` again (new uploads + new config).  
2. Restart `streamlit run app.py`.  
3. Do not copy old IDs from an old `app.py` comment.

---

## Run timed out after 2 minutes

The question may require too much processing.

Try:

```text
What are the top 3 Regions by total Sales? Use pandas, answer in 2 sentences.
```

---

## CFO still answers HR questions

### Check

- Sidebar really shows **CFO** and **2** authorized files.  
- You switched role *before* asking (toast “Chat cleared”).  

### If model still hallucinates HR names

Say: “In production we enforce at the data layer; the PoC attaches files only—model should not invent HR rows without the file.”

Re-ask: `Do you have the HR CSV attached? List attached datasets only.`

---

## Streamlit issues

### App keeps rerunning / loses state

Normal Streamlit behavior. Use sidebar **New chat** intentionally.

### Port in use

```bash
streamlit run app.py --server.port 8502
```

---

## Deprecation warning (Assistants API)

You may see a deprecation warning in the terminal. Suppressed in `app.py` for cleaner demos. For a long-term product, plan migration to OpenAI’s **Responses API** / Agents SDK. Fine for a 24h interview PoC.

---

## Still stuck?

1. Read [README.md](README.md) Quick start.  
2. Walk [DEMO.md](DEMO.md) exactly—no extra prompts.  
3. Check [platform.openai.com/usage](https://platform.openai.com/usage) for quota and spend.
