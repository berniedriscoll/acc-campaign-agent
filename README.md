# ACC Campaign Agent

> Multi-agent Adobe Campaign Classic pipeline powered by Claude.  
> Brief → Strategy → Angle Jury → Workflow + Content → QA → HITL → Compile.

---

## Overview

The ACC Campaign Agent turns a free-text campaign brief into a production-ready Adobe Campaign Classic (ACC) package — workflow XML and personalised email HTML — using a 10-stage multi-agent pipeline. LLMs handle all reasoning, strategy, and copywriting. Python enforces all contracts, rules, and gate logic deterministically. A human reviewer holds final approval before anything compiles.

Built for **Marriott Bonvoy** campaigns. Multi-brand ready — add a new entry to `config.py` and the entire pipeline adapts automatically.

---

## Pipeline — 10 Stages

```
Brief Strategist          Stage 1  — parse free-text brief → structured intent + signals
Retrieval + Contract      Stage 2  — validate targeting signals; build targeting SQL
Content Strategist        Stage 3  — generate 3–5 messaging angles
Angle Jury                Stage 4  — 3 parallel Claude voters → majority vote selects angle
                                     ┌─────────────────────┐
Workflow Architect    ─── Stage 5 ───┤  runs in parallel   ├─── Content Author
Workflow Lint             Stage 6   └─────────────────────┘    Content Lint
Workflow Critic           Stage 7   (both tracks parallel)     Content Critic
Gate Aggregator           Stage 8  — merge both tracks → pass / fail
HITL Approval             Stage 9  — human reviewer: approve / reject / needs_revision
Compile + Validate        Stage 10 — generate ACC workflow XML + email HTML
```

---

## Folder Structure

```
acc-campaign-agent/
├── app.py                    ← Streamlit UI (run this to use the agent)
├── run.py                    ← CLI entry point
├── orchestrator.py           ← Pipeline controller
├── config.py                 ← All signals, rules, thresholds, brand voice
│
├── models/
│   ├── brief.py              ← CampaignBrief, StructuredBrief
│   ├── campaign.py           ← MessagingAngle, CampaignPackage
│   ├── workflow.py           ← AccWorkflow, WorkflowStep
│   └── content.py            ← CampaignContent, EmailModule
│
├── agents/                   ← LLM layer (Claude API)
│   ├── base.py               ← Shared call_llm / call_llm_json
│   ├── brief_strategist.py   ← Stage 1
│   ├── content_strategist.py ← Stage 3
│   ├── angle_jury.py         ← Stage 4 — 3 parallel voters
│   ├── workflow_architect.py ← Stage 5a
│   ├── content_author.py     ← Stage 5b
│   ├── workflow_critic.py    ← Stage 7a
│   └── content_critic.py     ← Stage 7b
│
├── python/                   ← Deterministic enforcement layer
│   ├── retrieval.py          ← Load profiles, stays, suppressions
│   ├── contract.py           ← Validate signals; build targeting SQL
│   ├── workflow_lint.py      ← Schema rules (step types, counts, SQL)
│   ├── content_lint.py       ← Char limits, required modules, word count
│   ├── gate_aggregator.py    ← Merge both tracks → unified pass/fail
│   ├── compiler.py           ← Generate ACC XML + email HTML
│   └── variants.py           ← Bonvoy tier variants + token resolver
│
├── hitl/
│   └── approval.py           ← Human-in-the-loop approval gate
│
├── docs/
│   ├── ACC_Campaign_Agent_Brand_Voice.docx   ← Brand voice & styling reference
│   └── brand_voice_doc.js                   ← Doc build script (docx-js)
│
└── output/                   ← Compiled files (gitignored)
    ├── *_workflow.xml
    ├── *_email.html
    └── *_package.json
```

---

## Quickstart

### 1. Install dependencies

```bash
pip install anthropic streamlit python-dotenv pandas
```

### 2. Set your API key

```bash
# In your .env file (project root):
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run the UI

```bash
cd acc-campaign-agent
streamlit run app.py
```

Open **http://localhost:8502**

### 4. Or run from the CLI

```bash
# Demo campaign (Vail Oktoberfest) — auto-approves, no prompt
python run.py --demo --auto-approve

# Load a brief from JSON
python run.py --brief my_brief.json

# Interactive guided brief builder
python run.py
```

---

## The Streamlit UI

The UI is a three-panel interface that runs after a campaign is generated.

### Brief Panel (left)
- 3 presets: Vail Oktoberfest 2026 · NYC New Year's Eve · Miami Summer Escape
- Or enter a custom brief via the form fields
- Set number of messaging angles (2–6)

### Pipeline Log (right)
- Each of the 10 stages appears live as it completes
- Colour coded: ✅ green (pass) · ⚠️ amber (warn/gate fail) · ❌ red (error)
- Stage 9 (HITL) updates in-place when you submit your verdict
- Stage 10 (Compile) only runs after approval

### Results — Three Panels

| Panel | Contents |
|---|---|
| **Approve** | Lint scores, critic scores (0–100), blocking issues, `approve / reject / needs_revision` verdict form, structured JSON output |
| **Variant Preview** | Bonvoy tier selector (Member → Ambassador Elite + 2 edge cases), persona narrative, sample field data table |
| **Email Preview** | 6 tabs — see below |

### Email Preview Tabs

| Tab | What it shows |
|---|---|
| **Simulated Preview** | Email rendered with tokens resolved for the selected variant |
| **Raw Tokens (ACC)** | Email rendered with `{{tokens}}` highlighted yellow, `@@ACC tokens@@` highlighted orange |
| **HTML Source** | Full raw HTML as copyable code + ⬇️ Download button |
| **Workflow XML** | Full ACC workflow XML + ⬇️ Download button |
| **Angles & Jury** | All angles generated, winning angle, jury vote tally |
| **Workflow** | Step-by-step workflow, entry/exit signals, targeting SQL |

---

## Brand Voice & Styling

Brand identity is applied across three separate layers:

### 1. LLM Instruction — `config.py`

```python
BRAND_VOICE = {
    "Marriott Bonvoy": {
        "tone":     "aspirational, warm, rewarding",
        "avoid":    ["pushy", "salesy", "cheap", "discount"],
        "prefer":   ["exclusive", "curated", "earned", "experience", "points"],
        "sign_off": "The Marriott Bonvoy Team",
    }
}
```

Every LLM agent reads `BRAND_VOICE.get(brief.brand, {})` — tone, preferred vocabulary, and banned words are baked into the system prompt of the Content Strategist, Content Author, and Content Critic. To add a second brand, add a new key. No other changes required.

### 2. Deterministic Enforcement — `python/content_lint.py`

```python
CONTENT_RULES = {
    "subject_max_chars":   60,
    "preheader_max_chars": 90,
    "cta_max_chars":       35,
    "min_modules":         3,
    "required_modules":    ["hero", "cta"],
    "max_word_count":      350,
    "required_tokens":     [],     # e.g. ["{{first_name}}"] to enforce
}
```

The lint layer runs after the LLM writes copy — it enforces hard constraints the model cannot override. Failures block the gate. The critic score threshold (default 70/100) is set in `GATE_THRESHOLDS`.

### 3. HTML Compiler — `python/compiler.py`

Fixed Marriott Bonvoy visual identity applied to every email:

| Element | Value |
|---|---|
| Navy | `#1A3A5C` — header bar, hero, headings |
| Gold | `#C9A84C` — brand name, CTA button |
| Body font | Georgia, serif |
| Hero headline | 28px, font-weight normal |
| CTA | Uppercase, letter-spacing 1px |
| Container width | 600px, centred |

Full reference: [`docs/ACC_Campaign_Agent_Brand_Voice.docx`](docs/ACC_Campaign_Agent_Brand_Voice.docx)

---

## Targeting Signals

Signals are defined in `config.py` and map to ACC schema fields. The Brief Strategist selects signals from the brief; the Contract layer validates them and builds the targeting SQL.

| Signal | ACC Field | Condition |
|---|---|---|
| `email_eligible` | `EMAIL_OPT_IN` | `= 1` *(always enforced)* |
| `gold_elite` | `TIER` | `= 'GOLD'` |
| `platinum_elite` | `TIER` | `IN ('PLATINUM','TITANIUM','AMBASSADOR')` |
| `past_guest` | `STAY_COUNT` | `> 0` |
| `lapsed` | `LAST_STAY_DATE` | `< DATEADD(day, -365, GETDATE())` |
| `upcoming_res` | `NEXT_CHECKIN_DATE` | `IS NOT NULL` |
| `geo_filter` | `HOME_MARKET` | `= '{value}'` |
| `clv_high` | `CLV_SEGMENT` | `= 'HIGH'` |
| `app_download` | `HAS_APP` | `= 1` |
| `new_account` | `ACCOUNT_STATUS` | `= 'NEW'` |

---

## Member Tier Variants

The Variant Preview panel ships with 8 personas to stress-test all personalisation branches:

| Variant | Tests |
|---|---|
| Member — Has Points Balance | Standard path: firstName + points both present |
| Silver Elite — Moderate Points | Mid-tier messaging |
| Gold Elite — High Points Balance | Primary target segment |
| Platinum Elite — Strong Points | High-frequency traveller tone |
| Titanium Elite — No Points Data | Points-absent fallback (`{{points_balance}}` → "your points") |
| Ambassador Elite — Premium Points | VIP / ultra-high-value treatment |
| *(Edge)* Member — No First Name | Greeting fallback — must not render raw token |
| *(Edge)* Silver — No Name, No Points | Worst-case double fallback |

---

## Gate Logic

Both the workflow and content tracks must pass before the campaign reaches the human reviewer:

```
Workflow lint PASS  +  Workflow critic ≥ 70
        AND
Content lint PASS   +  Content critic  ≥ 70
        ↓
Gate PASSED → HITL
        ↓
HITL approved → Compile
```

If the gate fails, the HITL panel surfaces all blocking issues. The reviewer can approve with override, reject, or mark as needs revision.

---

## Output Files

Every approved campaign writes three files to `output/`:

| File | Contents |
|---|---|
| `*_workflow.xml` | ACC-formatted workflow definition with targeting SQL and step sequence |
| `*_email.html` | Fully compiled email with brand styling and personalisation tokens intact |
| `*_package.json` | Campaign summary — ID, angle, subject, gate result, verdict, file paths |

---

## Configuration Reference

All configuration lives in `config.py`. No code changes needed for most adjustments:

| Setting | Key | Default |
|---|---|---|
| LLM model | `LLM_MODEL` | `claude-opus-4-6` |
| Max tokens | `LLM_MAX_TOKENS` | `4096` |
| Min critic score (gate) | `GATE_THRESHOLDS` | `70 / 100` |
| Subject line max | `CONTENT_RULES` | `60 chars` |
| Preheader max | `CONTENT_RULES` | `90 chars` |
| Email frequency cap | `CAP_RULES` | `3 / 7d, 8 / 30d` |
| Max workflow steps | `WORKFLOW_RULES` | `12` |

---

## Requirements

```
anthropic>=0.86.0
streamlit>=1.55.0
python-dotenv
pandas
```

Python 3.11+

---

## Repository

**GitHub:** [berniedriscoll/acc-campaign-agent](https://github.com/berniedriscoll/acc-campaign-agent)
