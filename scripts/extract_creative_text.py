"""Regenerate source/creative_text.csv from the ad images in source/.

One vision-model call per image extracts the on-image text (OCR) and a short
visual description. The output CSV is committed, so this script only needs to
run when the creatives change — seeding reads the CSV and never calls any API.

Usage:
    uv run python scripts/extract_creative_text.py

Requires OPENAI_API_KEY in the environment/.env. Costs one small vision call
per image (7 total).
"""

import base64
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from openai import OpenAI  # noqa: E402

from app.core.config import settings  # noqa: E402

SOURCE_DIR = PROJECT_ROOT / "source"
OUTPUT_CSV = SOURCE_DIR / "creative_text.csv"

PROMPT = """You are extracting text and a description from a marketing ad image.
Return a JSON object with exactly these keys:
- "ocr_headline": the main headline text on the image, verbatim
- "ocr_body": the supporting body/subtext, verbatim
- "ocr_cta": the call-to-action button text verbatim, or "" if there is no button
- "vision_description": 2-3 sentences describing the visual composition
  (layout, imagery, colors, logo placement). Mention if there is no CTA button.
Transcribe exactly what is legible; do not invent text."""


def load_ad_images() -> list[tuple[str, str]]:
    with (SOURCE_DIR / "ad_set.csv").open(newline="", encoding="utf-8") as f:
        return [(row["ad_id"], row["image"]) for row in csv.DictReader(f, delimiter=";")]


def extract(client: OpenAI, image_path: Path) -> dict:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()
    response = client.chat.completions.create(
        model=settings.llm_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )
    return json.loads(response.choices[0].message.content)


def main() -> None:
    client = OpenAI(api_key=settings.openai_api_key)
    fields = ["ad_id", "ocr_headline", "ocr_body", "ocr_cta", "vision_description"]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for ad_id, image in load_ad_images():
            data = extract(client, SOURCE_DIR / image)
            writer.writerow({"ad_id": ad_id, **{k: data.get(k, "") for k in fields[1:]}})
            print(f"extracted: {ad_id}")

    print(f"wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
