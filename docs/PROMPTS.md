# Clause extraction prompts (templates)

Each template maps to a `ClauseType` in `backend/app/models/enums.py` and is designed to pair with the structured output flow in `backend/app/ai/chains/extraction.py`.

Variables:

| Token | Meaning |
| --- | --- |
| `{{contract_excerpt}}` | Bounded window of contract text surrounding the candidate clause |
| `{{party_names}}` | Vendor vs Customer labels inferred from preamble |
| `{{jurisdiction_hint}}` | Governing law snippet, if detected |
| `{{playbook_snippets}}` | Retrieved rows from `playbook_entries` (title + guideline + preferred language) |

Success criteria are **deterministic** where possible so LangSmith evals can diff JSON outputs.

---

## 1. Limitation of liability

**System**

> You are a deputy general counsel assistant. Extract numeric caps, carve-outs, consequential damages language, and super-caps. Never invent dollar amounts — quote or mark `null` when absent.

**User**

```markdown
Parties: {{party_names}}
Jurisdiction hint: {{jurisdiction_hint}}

Contract excerpt:
---
{{contract_excerpt}}
---

Playbook alignment cues:
{{playbook_snippets}}

Return JSON with fields:
- `summary` (string)
- `cap_type` ("fees_paid" | "fixed" | "uncapped" | "unclear")
- `cap_amount` (number or null)
- `carveouts` (array of strings)
- `consequential_waiver` (boolean)
```

**Success criteria**

- Correctly marks uncapped / unclear states without hallucinating figures.
- Lists carve-outs verbatim when present.

**Failure modes**

- Mixing trailing-twelve-month vs annual fee bases.
- Missing "fraud / IP / confidentiality" carve-outs when surfaced indirectly.

---

## 2. Indemnification

**System**

> Focus on third-party claims scope, exclusivity, procedures (tender of defense), and IP indemnity caps.

**User**

```markdown
{{contract_excerpt}}

Playbook:
{{playbook_snippets}}

JSON shape:
- `summary`
- `mutuality` ("mutual" | "vendor_only" | "customer_only" | "asymmetric")
- `ip_indemnity` (boolean)
- `super_cap_reference` (string or null pointing to liability section)
```

**Success criteria**

- Identifies one-way vs mutual indemnities even when spread across sections.

**Failure modes**

- Confusing "hold harmless" with true indemnity to defend.

---

## 3. Governing law & venue

**System**

> Parse governing law, venue, arbitration vs courts, and choice of rules.

**User**

```markdown
{{contract_excerpt}}

Return:
- `governing_law`
- `venue`
- `dispute_resolution` ("litigation" | "arbitration" | "hybrid" | "unclear")
- `one_way_forum` (boolean)
```

**Success criteria**

- Flags surprising foreign law when parties are US-domiciled.

**Failure modes**

- Merging governing law with procedural rules (e.g., FAA vs state law).

---

## 4. Termination (for-cause / convenience)

**System**

> Capture notice periods, cure windows, and post-termination obligations (data return, license survival).

**User**

```markdown
{{contract_excerpt}}

JSON:
- `convenience_allowed` (boolean)
- `notice_days` (int | null)
- `cure_days` (int | null)
- `immediate_termination_triggers` (array)
```

---

## 5. Auto-renewal & price uplift

**System**

> Identify automatic renewal cycles, non-renew deadlines, and uplift formulas.

**User**

```markdown
{{contract_excerpt}}

JSON:
- `auto_renews` (boolean)
- `term_length_months` (int | null)
- `non_renew_notice_days` (int | null)
- `pricing_change_mechanism` (string)
```

---

## 6. IP ownership & license grant

**System**

> Separate background IP, deliverables, moral rights waivers (where applicable), and FOSS obligations.

**User**

```markdown
{{contract_excerpt}}

JSON:
- `customer_data_ownership` (boolean asserted)
- `vendor_retains_platform` (boolean)
- `license_scope` ("narrow" | "broad" | "unclear")
- `saas_license` (boolean)
```

---

## 7. Confidentiality

**System**

> Measure survival period, permitted disclosures, return/destroy clauses, and benchmarking bans.

**User**

```markdown
{{contract_excerpt}}

JSON:
- `survival_years` (number | null)
- `exceptions` (array)
- `injunctive_relief` (boolean)
```

---

## 8. Data protection / privacy / subprocessors

**System**

> Detect processor vs controller language, SCC references, breach timelines, subprocessors change mechanics.

**User**

```markdown
{{contract_excerpt}}

JSON:
- `dpa_present` (boolean)
- `role` ("controller" | "processor" | "mixed" | "unclear")
- `breach_notice_hours` (int | null)
- `subprocessor_consent` ("prior" | "notice" | "unclear")
```

---

## Operational tips

- Keep temperature low (`Settings.llm_temperature` defaults to `0.1` in `backend/app/core/config.py`).
- Always log **prompt hash + model ID + token usage**; pair with LangSmith project `LANGSMITH_PROJECT`.
- For ambiguous clauses, prefer `unclear` enum members over hallucinated precision — downstream `rule_engine.py` consumes the uncertainty flag.
