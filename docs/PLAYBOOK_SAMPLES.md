# Playbook sample entries (worked examples)

Each row mirrors what `backend/scripts/seed_playbook.py` loads into `playbook_entries` — operational teams can extend this corpus per tenant. Risk mapping aligns with `RiskLevel` in `backend/app/models/enums.py`.

Legend:

- **Risky vendor language** — negotiated phrasing we often see from counterparties.
- **Approved fallback** — closer to customer-standard paper.
- **Redline rationale** — what to tell the business sponsor.
- **Risk mapping** — how auto-metrics should score the deviation.

---

## 1. Limitation of liability

**Risky vendor language**

> Except for either party's gross negligence or willful misconduct, each party's total liability for any claim arising out of this agreement shall not exceed five thousand dollars (US$5,000), regardless of the form of action.

**Approved fallback**

> Except for a party's breach of confidentiality, infringement of the other party's intellectual property rights, fraud, or willful misconduct, each party's aggregate liability arising out of or related to this agreement shall not exceed the fees paid by Customer to Vendor in the twelve (12) months preceding the claim.

**Redline rationale**

The vendor attempts a **static micro-cap** detached from contract value, eliminating meaningful recourse for service failures while preserving unlimited exposure for the vendor's own IP claims. Tie the cap to **fees paid** to preserve proportionality and carve out IP/confidentiality/fraud.

**Risk mapping**

- `RiskLevel.HIGH` when cap is fixed under trailing-twelve-month fees or uses a de minimis amount.
- Elevate to critical if consequential damages are broadly disclaimed without mutual symmetry.

---

## 2. Indemnification (third-party claims)

**Risky vendor language**

> Vendor shall have no indemnification obligations except for claims that Vendor has been finally adjudicated to have caused by its willful misconduct.

**Approved fallback**

> Each party shall defend and indemnify the other against third-party claims arising from the indemnifying party's (a) gross negligence or willful misconduct, (b) violation of law, or (c) infringement of the other party's intellectual property caused by the indemnifying party's platform when used in accordance with this agreement.

**Redline rationale**

Indemnity delayed until "final adjudication" effectively transfers defense costs and injunctive risk to Customer during multi-year litigation. Mutual baseline + **tender of defense** mechanics protect both sides.

**Risk mapping**

- `RiskLevel.HIGH` when indemnity is unilateral or requires final judgment.
- `RiskLevel.MEDIUM` when carve-outs omit IP or data-protection claims.

---

## 3. Governing law & venue

**Risky vendor language**

> This Agreement is governed by the laws of [Vendor's offshore jurisdiction], and Vendor may bring suit in any court of its choosing.

**Approved fallback**

> This Agreement is governed by the laws of the State of [Customer HQ], without regard to conflict-of-law principles. Each party irrevocably consents to the exclusive jurisdiction of the state and US federal courts located in [Customer preferred forum].

**Redline rationale**

One-sided **forum shopping** increases travel cost, unclear precedent, and enforcement risk. Choose a forum aligned with Customer operations while keeping exclusive jurisdiction mutual.

**Risk mapping**

- `RiskLevel.HIGH` for unilateral forum selection + non-recognized foreign law.
- `RiskLevel.LOW` once symmetrical and tied to known precedent.

---

## 4. Termination for convenience / cause

**Risky vendor language**

> Vendor may terminate this Agreement immediately for any reason. Customer may terminate only if Vendor materially breaches and fails to cure within one business day.

**Approved fallback**

> Either party may terminate for convenience with sixty (60) days' prior written notice. Either party may terminate for material breach if the breach is not cured within thirty (30) days (ten (10) days for payment defaults) after written notice.

**Redline rationale**

Asymmetric termination lets Vendor strand Customer mid-implementation while Customer cannot exit without proving breach on an impossible cure timeline.

**Risk mapping**

- `RiskLevel.HIGH` if only Vendor retains convenience termination.
- Flag `RiskLevel.MEDIUM` when data export windows are absent post-termination.

---

## 5. Auto-renewal & pricing escalators

**Risky vendor language**

> This Agreement renews automatically for successive one-year terms at Vendor's then-current list price without further notice.

**Approved fallback**

> The Agreement renews for successive one-year terms unless either party provides not less than sixty (60) days' notice of non-renewal. Any fee increase shall not exceed three percent (3%) or the US CPI-U, whichever is greater, absent mutual written amendment.

**Redline rationale**

Silent auto-renewals at **list price** enable unconstrained uplifts. Notice + inflation cap preserves budget predictability.

**Risk mapping**

- `RiskLevel.HIGH` when uplift is uncapped and non-renew windows < 60 days.
- Pair with procurement playbook for competitive bidding triggers.

---

## 6. IP ownership & SaaS license grant

**Risky vendor language**

> Vendor owns all deliverables and grants Customer a limited license terminating upon payment default, including Customer Data aggregated analytics.

**Approved fallback**

> Customer retains all rights to Customer Data. Vendor retains rights to the Vendor Platform. Deliverables are licensed to Customer on a perpetual, worldwide, non-exclusive basis for internal business purposes upon full payment.

**Redline rationale**

Ownership grab on deliverables + **data monetization** conflicts with Customer confidentiality and regulatory duties. Separate platform vs deliverables vs data.

**Risk mapping**

- `RiskLevel.HIGH` if Customer Data can be monetized or license ends automatically on immaterial default.
- `RiskLevel.MEDIUM` when deliverables are work-made-for-hire ambiguous.

---

## 7. Confidentiality (mutual)

**Risky vendor language**

> Confidential Information excludes everything disclosed orally or summarized in email. Either party may disclose the other's information to unlimited affiliates without restriction.

**Approved fallback**

> Confidential Information means non-public information designated as confidential or that reasonably should be understood as confidential. Each party will use the same degree of care as it uses for its own information (no less than reasonable care). Disclosures to affiliates, subprocessors, or legal advisors require a written confidentiality obligation.

**Redline rationale**

Overbroad exclusions eviscerate protection; unlimited affiliate disclosures leak sensitive pricing across corporate families.

**Risk mapping**

- `RiskLevel.HIGH` when oral disclosures unprotected + affiliates unbounded.
- Survival: ensure 3–5 year floor (see models for downstream audit expectations).

---

## 8. Data protection / processor terms

**Risky vendor language**

> Customer is solely responsible for compliance with all privacy laws; Vendor may use subprocessors without notice and store data in any region.

**Approved fallback**

> The parties will execute the Data Processing Addendum (Exhibit A) incorporating Standard Contractual Clauses where required. Vendor will maintain a subprocessor register and provide at least thirty (30) days' notice ofnew subprocessors, allowing Customer to object on reasonable data-protection grounds.

**Redline rationale**

One-sided GDPR/GDPR-like duties + blind subprocessoring breaks regulatory reality for enterprises. Align with `PlaybookEntry.clause_type = data_protection` seeds in the ORM layer.

**Risk mapping**

- `RiskLevel.CRITICAL` if cross-border transfers lack SCCs/BCRs where EU/UK data exists.
- `RiskLevel.MEDIUM` when breach notification windows exceed 72 hours.

---

## How reviewers should use these samples

1. Match extracted clause to `clause_type` string used in retrieval (`playbook_entries.clause_type`).
2. Compare embeddings similarity scores; investigate false positives below **0.82 cosine similarity**.
3. Annotate accepted redlines in LangSmith so NLP teams can refine prompts in `ai/prompts.py`.

---

## Expansion guidelines for your own playbook grid

- **Maximum 256 chars** for `title` per DB constraint — keep crisp.
- Prefer storing **long-form rationale** in `guideline` and polished replacement language in `preferred_language`.
- When lawyers approve new canonical language, re-embed and run `ANALYZE` on the vector index.

---

## Quality assurance loop

| Step | Owner | Artifact |
| --- | --- | --- |
| Intake risky clause | Reviewer | LangSmith annotation |
| Map risk | System | `risk.py` output |
| Update playbook row | Admin API | `PlaybookEntry` revision |
| Reindex | Platform | `make vector.index` |
| Regression eval | ML engineer | Dataset row |

Maintain CSV exports for **outside counsel** audits quarterly.

---

## Synthetic negative examples (for training evaluators)

1. **Merged sections** — liability + indemnity + warranty in one paragraph; ensure extraction splits correctly before playbook mapping.
2. **Defined terms drift** — capitalized term not in exhibit; require human fallback.
3. **Non-English fragments** — dual-language MSAs; OCR ordering may scramble clauses — flag in `document_text.py`.

Document outcomes of these adversarial samples in `tests/eval/cases/` as they arrive.

---

## Reference table — clause_type strings

Use these consistently across seeds, prompts, and analytics dashboards:

| clause_type | Display name |
| --- | --- |
| `limitation_of_liability` | Limitation of liability |
| `indemnification` | Indemnification |
| `governing_law` | Governing law & venue |
| `termination` | Termination |
| `auto_renewal` | Auto-renewal & pricing |
| `ip_ownership` | IP ownership & license |
| `confidentiality` | Confidentiality |
| `data_protection` | Data protection / privacy |

If product introduces novel clause families (e.g., SLAs, exclusivity), extend this table **before** writing prompts so `ClauseType` and analytics stay aligned.

## Tone & voice guidance for playbook authors

1. Prefer **plain English** in `guideline` (internal voice) even when `preferred_language` remains legalistic.
2. Avoid absolutist words like "never" unless policy truly mandates — models imitate statistical patterns from wording.
3. Cross-link **defined terms** only when the playbook snippet includes the definition anchor; otherwise use descriptive nouns.

## Metric hooks

Suggested analytics events when playbook entries are consumed:

```json
{
  "event": "playbook_matched",
  "clause_type": "limitation_of_liability",
  "similarity": 0.88,
  "playbook_entry_id": "uuid",
  "contract_id": "uuid"
}
```

Instrument the FastAPI layer when routers land so product can graph **accepted vs rejected** playbook suggestions per clause family.

---

## Closing note

Playbooks are **living documents**. Legal Agent encodes them as rows + vectors so product teams can iterate faster than static PDF checklists — but lawyers remain the ultimate source of truth.
