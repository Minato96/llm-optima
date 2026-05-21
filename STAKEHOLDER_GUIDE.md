# Stakeholder presentation guide

Talking points for **executive demos**, **architecture reviews**, and **product stakeholders**—including *“Why build custom glue instead of only buying platforms?”*

---

## Elevator pitch (30 seconds)

> This is a governed financial Q&A proof of concept. Executives ask questions in natural language; OpenAI’s Code Interpreter runs real pandas and matplotlib on enterprise CSVs. Custom code is intentionally thin: Streamlit UI, role-based file attachment so the CFO never receives HR payroll, cost controls, and structured feedback. We maximize managed AI services and minimize bespoke code—the same philosophy as enterprise low-code, with explicit control over security and integration.

---

## Requirements coverage

| Requirement | How this project addresses it |
|-------------|-------------------------------|
| Upload / use files | `setup.py` uploads CSVs; threads attach by `file_id` |
| CEO sees N files | Sales + HR + Market (3) |
| CFO sees N−2 | Sales + Market only (HR excluded) |
| Natural language prompts | Streamlit chat |
| Run Python | OpenAI Code Interpreter (pandas) |
| Visualizations | matplotlib in sandbox; user asks for “bar chart” / “line plot” |
| Business questions | Profit, attrition, workforce planning—via NL prompts |

---

## “Why not use existing tools?”

**Agree first, then narrow:**

> We did not rebuild a BI suite or a foundation model. We composed OpenAI + Streamlit to validate the **workflow** and **access model** quickly.

| Tool category | Why it’s not a 1:1 replacement for this PoC |
|---------------|---------------------------------------------|
| **Power BI / Tableau** | Strong for dashboards; weaker for ad-hoc executive questions without full semantic modeling |
| **Copilot for M365 / Fabric** | Right for mature Microsoft estates; this PoC shows API-level RBAC before platform commitments |
| **ChatGPT custom GPTs** | Similar UX; this build shows **per-role file attachment** and reproducible setup in code |
| **LangChain / Flowise / n8n** | Could orchestrate the same flow; minimal Python was chosen for clarity and speed |

**When custom integration is justified:**

- Compliance: attach only allowed files per role  
- Cost control: conversation boundaries, row limits  
- Integration path: SSO + Fabric + Power Automate in production  

**When to standardize on platform tooling:**

- Organization already has Fabric + row-level security + Copilot licenses  
- Users primarily work in Teams / Excel  
- Governance team owns the semantic layer  

---

## Low-code / platform alignment

| Principle | This project |
|-----------|--------------|
| Ship fast | Streamlit + OpenAI APIs, ~250 lines custom code |
| Prefer managed services | LLM, sandbox, file hosting via OpenAI |
| Governance | RBAC via attachment list, not prompt-only rules |
| Iterate from PoC | `feedback_log.csv`, config file, documented setup |

**Typical production stack:**

```
Entra ID (login)
    → Power Apps or enterprise portal (UI)
    → Power Automate / Logic Apps (orchestration)
    → Azure OpenAI (enterprise contract)
    → Fabric / Snowflake / Dataverse (data + RLS)
```

This repository is the **clickable logical diagram** on the fastest path to validation.

---

## Strengths to emphasize

1. **RBAC at data attachment** — CFO never receives HR `file_id`; not reliance on the model to refuse.  
2. **Accurate math** — instructions require Python execution, not guessing.  
3. **Operational awareness** — rate limits, cost, `MAX_ROWS_PER_FILE`, conversation boundaries.  
4. **Transparent scope** — demo auth, API migration path, production gaps documented honestly.  

---

## Known limitations (framed for maturity)

| Limitation | Production response |
|------------|---------------------|
| Dropdown login | Entra ID and group → dataset mapping |
| Assistants API deprecated | Migrate to Responses / Agents SDK |
| API cost | Trimmed datasets, scripted demos, quotas per team |
| Charts require explicit prompts | Local chart renderer or governed plot tools |

---

## If stakeholders prefer “less custom code”

> The goal is integration and governance, not line count. The same outcomes map to wiring Copilot to permission-filtered SharePoint libraries or Fabric workspaces—the PoC proves the pattern before platform rollout.

---

## If stakeholders want deeper technical detail

> The security boundary is which files enter the sandbox. We can walk through `create_thread_with_files`, token growth in long threads, and row caps in setup—including options to move Python execution in-house for cost and residency.

---

## Discovery questions for the room (optional)

1. Which low-code or automation stack is standardized—Power Platform, ServiceNow, other?  
2. Where are data permissions enforced today—warehouse RLS or application layer?  
3. Are agents primarily internal copilots or customer-facing?  

---

## Delivery narrative

> Initial effort focused on a vertical slice: upload, chat, RBAC. Subsequent work hardened reliability—smaller files after rate limits, conversation design for follow-ups, chart behavior, feedback logging, and documentation. That mirrors a sensible production rollout: prove value, then harden.

---

## Code walkthrough (if requested)

1. `app.py` — `ROLE_ACCESS`, `create_thread_with_files`  
2. `setup.py` — `MAX_ROWS_PER_FILE`, upload, `openai_config.json`  
3. [ARCHITECTURE.md](ARCHITECTURE.md) — diagrams  

---

## Live demo

Follow **[DEMO.md](DEMO.md)** exactly for stakeholder presentations—avoid unscripted prompt spam that increases cost and failure rates.
