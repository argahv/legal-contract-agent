# Map-Reduce Extraction (v2026-01-30)

You segment **one chunk** of an agreement. Return JSON `clauses[]` with `title`, `clause_type`,
`body` (verbatim from chunk), and `confidence` in [0,1].

Focus on seven buckets when present in the chunk:
`limitation_of_liability`, `indemnification`, `governing_law`, `termination`,
`intellectual_property`, `confidentiality`, `data_protection`.

If none apply, return an empty `clauses` array or mark `uncategorized` only when truly required.
