"""Seed starter playbook entries — idempotent, no embeddings (indexer fills later)."""

from __future__ import annotations

import asyncio
import sys

from app.db.session import AsyncSessionLocal
from app.models.playbook import PlaybookEntry
from app.repositories.playbook_repository import PlaybookRepository

_STARTER: list[dict[str, str | None]] = [
    {
        "title": "Limitation of liability — dual cap",
        "clause_type": "limitation_of_liability",
        "guideline": "Cap direct damages at fees paid in trailing 12 months; carve out fraud & IP.",
        "preferred_language": "Except for a Party's breach of confidentiality or infringement of the other's "
        "intellectual property rights, each Party's aggregate liability arising out of this Agreement shall not "
        "exceed the fees paid by Customer to Vendor in the twelve (12) months preceding the claim.",
    },
    {
        "title": "Indemnification — mutual narrow baseline",
        "clause_type": "indemnification",
        "guideline": "Mutual indemnity for third-party IP/bodily injury to the extent caused by a party; "
        "cap to annual fees unless carve-outs trigger.",
        "preferred_language": "Each Party will defend and indemnify the other against third-party claims arising "
        "from the indemnifying Party's gross negligence, willful misconduct, or infringement of the other "
        "Party's intellectual property, subject to Section [X] (Liability Cap) except for excluded claims.",
    },
    {
        "title": "Governing law — buyer-favorable substantive law",
        "clause_type": "governing_law",
        "guideline": "Prefer customer's HQ state law absent strong vendor reason; avoid foreign law surprises.",
        "preferred_language": "This Agreement is governed by the laws of the State of [Customer HQ], without "
        "regard to conflicts-of-law principles that would apply another jurisdiction's laws.",
    },
    {
        "title": "Termination — for-cause + convenience with wind-down",
        "clause_type": "termination",
        "guideline": "Allow convenience exit with 60-90d notice; material breach cure period 30d (14d for payment).",
        "preferred_language": "Either Party may terminate this Agreement for convenience upon not less than "
        "sixty (60) days written notice. Either Party may terminate for material breach if such breach is not "
        "cured within thirty (30) days (ten (10) days for payment defaults) after written notice.",
    },
    {
        "title": "Auto-renewal — annual opt-out window",
        "clause_type": "auto_renewal",
        "guideline": "Disclose auto-renew; require 60d notice to non-renew; price uplift capped or CPI-indexed.",
        "preferred_language": "This Agreement will automatically renew for successive one-year terms unless "
        "either Party provides written notice of non-renewal at least sixty (60) days before the then-current "
        "term end. Any fee increase shall not exceed [3%] or CPI-U, whichever is greater, annually.",
    },
    {
        "title": "IP ownership — customer data vs deliverables",
        "clause_type": "ip_ownership",
        "guideline": "Customer owns its data; vendor retains platform; deliverables license: broad for customer.",
        "preferred_language": "Customer retains all rights in Customer Data. Vendor retains all rights in the "
        "Vendor Platform. Subject to payment, Vendor grants Customer a perpetual, worldwide, non-exclusive license "
        "to use Deliverables for Customer's internal business purposes.",
    },
    {
        "title": "Confidentiality — standard exceptions + GDPR-safe handling",
        "clause_type": "confidentiality",
        "guideline": "3-5y survival; exceptions for public, independent development, lawful disclosure; subprocessors DPAs.",
        "preferred_language": "Each Party will protect the other's Confidential Information with at least the "
        "same degree of care it uses for its own similar information, but not less than reasonable care, for a "
        "period of five (5) years following disclosure (or longer where required by law).",
    },
    {
        "title": "Data protection — SCCs + subprocessors list",
        "clause_type": "data_protection",
        "guideline": "Processor role, SCCs for EU transfers, DPA attached, breach notice 48-72h, subprocessors approval tiered.",
        "preferred_language": "The Parties will execute the Data Processing Addendum attached as Exhibit [A], "
        "incorporating the Standard Contractual Clauses where applicable. Vendor will maintain a subprocessor "
        "register and notify Customer of material changes in accordance with the DPA.",
    },
]


async def _run() -> int:
    async with AsyncSessionLocal() as session:
        repo = PlaybookRepository(session)
        if await repo.count() > 0:
            print("Playbook already contains rows — skipping seed.")
            return 0
        for row in _STARTER:
            await repo.add(
                PlaybookEntry(
                    title=str(row["title"]),
                    clause_type=str(row["clause_type"]),
                    guideline=str(row["guideline"]),
                    preferred_language=row.get("preferred_language"),
                    embedding=None,
                )
            )
        await session.commit()
        print(f"Seeded {len(_STARTER)} playbook entries (embeddings pending vector.index).")
    return 0


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_run()))
    except Exception as exc:
        print(f"seed_playbook failed: {exc}", file=sys.stderr)
        print("Hint: ensure DATABASE_URL is set and migrations created the playbook_entries table.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
