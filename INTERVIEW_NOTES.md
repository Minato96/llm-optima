# Interview notes

Talking points for presenting this project to a **low-code / AI tools** interviewer—especially if they ask *“Why build from scratch?”*

---

## Elevator pitch (30 seconds)

> I built a governed financial Q&A agent in under a day. Executives ask questions in natural language; OpenAI’s Code Interpreter runs real pandas and matplotlib on enterprise CSVs. My custom code is the thin layer: Streamlit UI, role-based file attachment so the CFO never gets HR payroll, cost controls, and feedback logging. I used maximum managed AI and minimum bespoke code—same mindset as low-code, but with explicit control over security and integration.

---

## Map to the original task

| Requirement | How this project addresses it |
|-------------|-------------------------------|
| Upload / use files | `setup.py` uploads CSVs; threads attach by `file_id` |
| CEO sees N files | Sales + HR + Market (3) |
| CFO sees N−2 | Sales + Market only (HR excluded) |
| Natural language prompts | Streamlit chat |
| Run Python | OpenAI Code Interpreter (pandas) |
| Visualizations | matplotlib in sandbox; user asks for “bar chart” / “line plot” |
| Business questions | Profit, attrition, firing—via NL prompts |

---

## “Why not use existing tools?”

**Agree first, then narrow:**

> I didn’t rebuild a BI suite or an LLM. I composed OpenAI + Streamlit to prove the **workflow** and **access model** in 24 hours.

| Tool category | Why it’s not a 1:1 replacement for this PoC |
|---------------|---------------------------------------------|
| **Power BI / Tableau** | Great for dashboards; weak for ad-hoc “who should we fire?” without modeling everything first |
| **Copilot for M365 / Fabric** | Right for mature Microsoft shops; this shows API-level RBAC when you’re proving a concept before platform commits |
| **ChatGPT custom GPTs** | Similar UX; this demo shows **file attachment per role** and reproducible setup in code |
| **LangChain / Flowise / n8n** | Could orchestrate the same flow; I chose minimal Python for speed and clarity in a take-home |

**When custom glue is justified:**

- Compliance: attach only allowed files per role  
- Cost control: thread-per-question, row limits  
- Integration path: later plug SSO + Fabric + Power Automate  

**When to stop coding and buy/platformize:**

- Org already has Fabric + row-level security + Copilot licenses  
- Users live in Teams / Excel  
- Governance team owns the semantic layer  

---

## Low-code alignment (speak their language)

| Low-code principle | This project |
|--------------------|--------------|
| Ship fast | Streamlit + OpenAI APIs, ~250 lines custom code |
| Prefer managed services | LLM, sandbox, file hosting = OpenAI |
| Governance | RBAC via attachment list, not prompt honor system |
| Iterate from PoC | `feedback_log.csv`, config file, clear setup script |

**Production low-code stack you’d propose:**

```
Entra ID (login)
    → Power Apps or Streamlit (UI)
    → Power Automate / Logic Apps (orchestration)
    → Azure OpenAI (enterprise contract)
    → Fabric / Snowflake / Dataverse (data + RLS)
```

Your PoC is the **logical diagram** with the fastest path to click-through.

---

## Strengths to emphasize

1. **RBAC at data attachment** — CFO lacks HR `file_id`; not just “please don’t look at HR.”  
2. **Accurate math** — instructions require Python, not guessing.  
3. **Operational awareness** — rate limits, cost, `MAX_ROWS_PER_FILE`, new thread per question.  
4. **Honest scope** — demo auth, deprecated API noted, migration path stated.  

---

## Weaknesses to acknowledge (shows maturity)

| Weakness | Your line |
|----------|-----------|
| Dropdown login | “Production uses Entra ID and group → file mapping.” |
| Assistants API deprecated | “PoC speed; migrate to Responses / Agents SDK.” |
| API cost | “Trimmed CSVs, scripted demo, thread-per-question.” |
| Charts inconsistent without explicit ask | “Prompt design + matplotlib instructions; prod could render charts locally.” |

---

## If they say you’re “too high-code”

> I can go deep on systems, but for this assignment I intentionally stayed at the integration layer—same job a low-code AI engineer does when wiring Copilot to SharePoint libraries with permission filters. The artifact is the **pattern**, not the line count.

---

## If they say you’re “not technical enough”

> The security boundary is which files enter the sandbox. I can walk through `create_thread_with_files`, token cost of long threads, and why I cap rows in setup. Happy to whiteboard moving Python execution on-prem for cost.

---

## Questions to ask them (optional, shows interest)

1. What low-code stack do you standardize on—Power Platform, ServiceNow, something else?  
2. Where do you enforce data permissions today—warehouse RLS or app layer?  
3. Are agents mostly internal copilots or customer-facing?  

---

## Time spent narrative (honest)

> I spent a few hours on the first vertical slice—upload, chat, RBAC. The rest went to reliability: cutting file size after rate limits, one thread per question, chart prompts, and documentation. That’s how I’d phase a real rollout too: prove value, then harden.

---

## Files to open if they ask “show me the code”

1. `app.py` — `ROLE_ACCESS`, `create_thread_with_files` (~10 lines that matter)  
2. `setup.py` — `MAX_ROWS_PER_FILE`, upload, `openai_config.json`  
3. [ARCHITECTURE.md](ARCHITECTURE.md) — diagram  

Do **not** scroll through `venv/`.

---

## Link to demo

Run the exact script in **[DEMO.md](DEMO.md)**—do not freestyle twenty prompts during the interview.
