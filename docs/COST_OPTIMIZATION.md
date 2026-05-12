# Cost optimization playbook

Legal workflows can explode token usage if each upload triggers unbounded context. This guide lists **proven** tactics mapped to Legal Agent modules.

## 1. Model tiering

| Stage | Model | Module |
| --- | --- | --- |
| Clause extraction | `gpt-4o-mini` (default in `Settings.openai_model`) | `ai/chains/extraction.py` |
| Risk reasoning / nuanced indemnity | `gpt-4o` or future `gpt-4.1` | `ai/chains/risk.py` |
| Embeddings | `text-embedding-3-small` | Playbook + clause vectors |

Escalate only when heuristics detect high stakes (super-cap breach, cross-border privacy).

## 2. Context trimming & chunking

- Hard cap extracted characters at `Settings.extracted_text_limit_chars`.
- Slide overlapping windows (e.g., 1.5k tokens, 150 token overlap) instead of sending entire MSAs in one prompt when length exceeds budget.
- Strip boilerplate (TOC, generic definitions) with lightweight regex before LLM — log removed spans for audit.

## 3. Batched embeddings

- When ingesting playbook CSVs, call OpenAI `/v1/embeddings` with batch arrays (per limits) instead of single texts sequentially.
- Schedule nightly rebuild windows (`make vector.index`) to leverage lower traffic periods.

## 4. Embedding & retrieval cache

- Cache embeddings keyed by `sha256(normalized_text)` in Redis or Postgres (`embedding_cache` table) before hitting OpenAI.
- Store last retrieval set with TTL (15–60 minutes) for active reviewer sessions — invalidates on new uploads.

## 5. Prompt compression

- Move static instructions into **system** prompts to maximize cache hits (OpenAI prompt caching when available).
- Use bullet summaries for playbook hints instead of pasting entire `preferred_language` paragraphs when similarity > 0.9.

## 6. Streaming UX vs batch APIs

- Stream final narratives to the UI to improve perceived latency even if total tokens identical.
- Avoid streaming for structured JSON extraction unless schema validated incrementally — prefer single round trip.

## 7. Semantic cache

- For near-duplicate vendor paper, reuse prior clause extractions when fingerprint (SimHash) matches within threshold — require lawyer opt-in per tenant for compliance.

## 8. Rate limiting alignment

`Settings.rate_limit_requests_per_minute` protects the API surface — align LLM concurrency pools so SlowAPI limits and OpenAI TPM limits don't fight each other.

## 9. Observability-driven tuning

- Track **cost per successful review** metric in your analytics stack (PostHog segment in optional module).
- Alert when p95 tokens per contract exceed rolling weekly average + 2σ.

## 10. Degraded modes

When spend caps trip:

1. Switch extraction entirely to `gpt-4o-mini`.
2. Disable automatic risk narration; keep deterministic `rule_engine.py`.
3. Queue playbook re-embedding jobs.

Document the degradation banner copy in the reviewer UI spec.
