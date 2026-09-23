#!/usr/bin/env python3
"""Rename Dara to Moras across the Postgres content, without touching file paths.

The artifact and the teaching documents were renamed to Moras; the seeded
assignment was not, so the student portal still says "Dara's Coffee Cart".

Rather than hard-coding a list of columns, this scans every text, varchar and
jsonb column in the public schema for the string, reports what it finds, and
(with --apply) rewrites those columns. "Dara's" becomes "Moras's" for free,
because the possessive is just the name plus an apostrophe.

Path-like columns are excluded on purpose. storage/.../dara_coffee_cart_brief.pdf
is a real file on disk; rewriting file_path or filename in the database would
point the document viewer at a file that does not exist.

    docker compose exec app python -m fiosra.mvp.rename_dara_to_moras          # dry run
    docker compose exec app python -m fiosra.mvp.rename_dara_to_moras --apply
    docker compose exec app python -m fiosra.mvp.rename_dara_to_moras --undo   # Moras -> Dara
"""

import argparse
import asyncio
import logging

from sqlalchemy import text

from fiosra.mvp.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Renaming these would break a lookup, not a label.
EXCLUDED_COLUMNS = {"file_path", "filename", "source_url", "url", "path", "mime_type"}

FIND_COLUMNS = """
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type IN ('text', 'character varying', 'jsonb')
ORDER BY table_name, column_name
"""


async def main(mode: str) -> None:
    old, new = ("Dara", "Moras") if mode != "undo" else ("Moras", "Dara")

    async with AsyncSessionLocal() as session:
        columns = (await session.execute(text(FIND_COLUMNS))).fetchall()

        hits = []
        for table_name, column_name, data_type in columns:
            if column_name in EXCLUDED_COLUMNS:
                continue
            # Cast to text so jsonb and varchar are counted the same way.
            probe = f'SELECT count(*) FROM "{table_name}" WHERE "{column_name}"::text LIKE :pat'
            try:
                count = (await session.execute(text(probe), {"pat": f"%{old}%"})).scalar()
            except Exception as exc:  # a view or a permission problem, not our business
                logger.debug("skipped %s.%s: %s", table_name, column_name, exc)
                continue
            if count:
                hits.append((table_name, column_name, data_type, count))

        if not hits:
            logger.info("No rows contain %r. Nothing to do.", old)
            return

        total = sum(h[3] for h in hits)
        logger.info("Found %r in %d column(s), %d row(s) total:", old, len(hits), total)
        for table_name, column_name, data_type, count in hits:
            logger.info("   %-28s %-22s %-18s %d row(s)", table_name, column_name, data_type, count)

        if mode == "dry-run":
            logger.info("DRY RUN - nothing written. Re-run with --apply to rename %r to %r.", old, new)
            return

        for table_name, column_name, data_type, _ in hits:
            if data_type == "jsonb":
                stmt = (
                    f'UPDATE "{table_name}" '
                    f'SET "{column_name}" = replace("{column_name}"::text, :old, :new)::jsonb '
                    f'WHERE "{column_name}"::text LIKE :pat'
                )
            else:
                stmt = (
                    f'UPDATE "{table_name}" '
                    f'SET "{column_name}" = replace("{column_name}", :old, :new) '
                    f'WHERE "{column_name}" LIKE :pat'
                )
            result = await session.execute(text(stmt), {"old": old, "new": new, "pat": f"%{old}%"})
            logger.info("   updated %s.%s (%d row(s))", table_name, column_name, result.rowcount)

        await session.commit()

        # Verify against the same probe the scan used.
        remaining = 0
        for table_name, column_name, _, _ in hits:
            probe = f'SELECT count(*) FROM "{table_name}" WHERE "{column_name}"::text LIKE :pat'
            remaining += (await session.execute(text(probe), {"pat": f"%{old}%"})).scalar() or 0
        if remaining:
            logger.warning("%d row(s) still contain %r.", remaining, old)
        else:
            logger.info("Verified: no remaining occurrences of %r.", old)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Rename Dara to Moras.")
    group.add_argument("--undo", action="store_true", help="Rename Moras back to Dara.")
    args = parser.parse_args()
    asyncio.run(main("apply" if args.apply else "undo" if args.undo else "dry-run"))
