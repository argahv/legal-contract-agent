# Scaling & multi-tenancy strategies

## Multi-tenancy models

| Approach | Pros | Cons |
| --- | --- | --- |
| Shared DB + tenant_id column | Simple ops | Risk of ORM leakage if queries forget filters |
| Schema per tenant | Strong isolation | Migration fan-out cost |
| Database per tenant | Maximum isolation | Expensive, ops heavy |

Recommendation for Legal Agent MVP → growth:

1. Start **shared DB** with mandatory `organization_id` foreign keys + pytest guards that attempt cross-tenant access.
2. Move regulated customers to **schema-per-tenant** using Postgres `search_path` per connection — Alembic upgrade must loop schemas.
3. Reserve **DB-per-tenant** for enterprise deals with dedicated Infosec reviews.

Row-Level Security (RLS) can enforce isolation even if application code regresses:

```sql
CREATE POLICY tenant_isolation ON contracts
  USING (organization_id = current_setting('app.current_tenant')::uuid);
```

Set `SET LOCAL app.current_tenant = '<uuid>'` at request start via SQLAlchemy event hooks.

## pgvector index tuning

- Start with **HNSW** when recall > throughput; use **IVFFLAT** when memory constrained.
- Build index **after** bulk seeding playbook embeddings.
- Tune `lists` (IVFFLAT) to `sqrt(rowcount)` rule-of-thumb; re-run `ANALYZE`.
- For hybrid queries (metadata + vector), maintain btree on `clause_type` with partial indexes.

## Request throttling layers

1. Edge (Cloudflare / AWS WAF) — shield DDoS.
2. API (`slowapi`) — per IP + per tenant key.
3. OpenAI client — internal semaphores + exponential backoff (`Settings.openai_max_retries`).

## Background work migration path

```mermaid
flowchart LR
  BT[FastAPI BackgroundTasks]
  ARQ[Arq worker]
  CEL[Celery + Redis]
  BT --> ARQ --> CEL
```

| Stage | Workloads |
| --- | --- |
| BackgroundTasks | OCR, single-doc embeddings |
| Arq | Scheduled playbook rebuild, webhooks |
| Celery | Large fan-out with broker HA |

## Cache tiers

| Data | Store | TTL |
| --- | --- | --- |
| Session / JWT denylist | Redis | minutes–hours |
| Embedding cache | Redis / Postgres | 24h |
| Static legal guidance | CDN | versioned |

## Cold-start mitigation

- Keep **minimum instances ≥1** on Cloud Run / Render for reviewer-facing API.
- Warm pools for workers right before business hours (cron).
- Use **Provisioned Concurrency** where available.

## Read replicas

- Serve analytics / auditor dashboards from replica to protect writer CPU.
- Ensure replicas lag monitor triggers alert > N seconds during heavy ETL.

## Capacity planning math

Approximate:

```text
peak_rps * avg_latency * workers_per_cpu ≈ required cores
```

Add 30% headroom for LLM-induced latency spikes (timeouts in `risk.py`).

## Failure drills

- Quarterly: kill primary DB → ensure HA failover success.
- Monthly: revoke API key → secrets rotation playbook.

See `docs/DEPLOYMENT.md` for operational runbooks tying these strategies to CI/CD.
