"""Seed the database from the CSV/PNG files in source/ and copy the ad
images into the static directory, renamed to `{uuid}_{slugified-title}.png`.
Originals in source/ are left untouched.

Usage:
    uv run python scripts/seed_from_source.py [--force]

--force truncates ads/ad_comments/ad_metrics before reseeding. Without it,
the script refuses to run if the ads table already has rows.
"""

import argparse
import asyncio
import csv
import re
import shutil
import sys
import uuid
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, select, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models import Ad, AdComment, AdMetric, AdPlatform  # noqa: E402

SOURCE_DIR = PROJECT_ROOT / "source"
STATIC_DIR = PROJECT_ROOT / settings.static_dir


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-")


def load_ads() -> list[dict]:
    with (SOURCE_DIR / "ad_set.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def load_comments() -> list[dict]:
    with (SOURCE_DIR / "comments.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_metrics() -> list[dict]:
    with (SOURCE_DIR / "metrics.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def copy_ad_image(ad_id: uuid.UUID, title: str, source_filename: str) -> str:
    source_path = SOURCE_DIR / source_filename
    if not source_path.exists():
        raise FileNotFoundError(f"image not found: {source_path}")

    new_filename = f"{ad_id}_{slugify(title)}{source_path.suffix}"
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(source_path), str(STATIC_DIR / new_filename))
    return new_filename


async def reset_tables() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("TRUNCATE TABLE ad_comments, ad_metrics, ads RESTART IDENTITY CASCADE")
        )
        await session.commit()


async def seed(force: bool) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Ad))
        if existing and not force:
            raise SystemExit(
                f"ads table already has {existing} row(s); rerun with --force to wipe and reseed"
            )

    if force:
        await reset_tables()

    ad_rows = load_ads()
    comment_rows = load_comments()
    metric_rows = load_metrics()

    async with AsyncSessionLocal() as session:
        ad_id_by_business_key: dict[str, uuid.UUID] = {}

        for row in ad_rows:
            ad_id = uuid.uuid4()
            ad_id_by_business_key[row["ad_id"]] = ad_id
            path = copy_ad_image(ad_id, row["title"], row["image"])
            session.add(
                Ad(
                    id=ad_id,
                    ad_id=row["ad_id"],
                    title=row["title"],
                    body=row["body"] or None,
                    image=row["image"],
                    path=path,
                )
            )
        await session.flush()

        for row in comment_rows:
            session.add(
                AdComment(
                    date=date.fromisoformat(row["date"]),
                    ad_id=row["ad_id"],
                    platform=AdPlatform(row["platform"]),
                    comment=row["comment"],
                )
            )

        for row in metric_rows:
            session.add(
                AdMetric(
                    date=date.fromisoformat(row["date"]),
                    ad_id=row["ad_id"],
                    platform=AdPlatform(row["platform"]),
                    impressions=int(row["impressions"]),
                    clicks=int(row["clicks"]),
                    engagements=int(row["engagements"]),
                )
            )

        await session.commit()

    print(
        f"seeded {len(ad_rows)} ads, {len(comment_rows)} comments, "
        f"{len(metric_rows)} metrics into {settings.database_url}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="truncate ads/ad_comments/ad_metrics before reseeding",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.force))


if __name__ == "__main__":
    main()
