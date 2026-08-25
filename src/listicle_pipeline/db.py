import csv
from functools import lru_cache

from .config import DATA_DIR
from .state import Company

CSV_PATH = DATA_DIR / "synthetic_tool_db.csv"

# top_lexical_kw / top_semantic_kw / top_intent_kw / secondary_keywords_json are
# leftover columns from an earlier prototype iteration. README §4b later decided
# keywords must be generated live per request, not stored, so they're ignored here.


def _row_to_company(row: dict) -> Company:
    return Company(
        company_name=row["company_name"],
        category=row["category"],
        positioning=row["positioning"],
        starting_price=row["starting_price"],
        aggregated_rating=float(row["aggregated_rating"]),
        review_count=int(row["review_count"]),
        what_it_does_well=[
            row[key]
            for key in ("what_it_does_well_1", "what_it_does_well_2", "what_it_does_well_3", "what_it_does_well_4")
            if row.get(key)
        ],
        gaps=[row[key] for key in ("gap_1", "gap_2") if row.get(key)],
        best_for=row["best_for"],
        website_url=row["website_url"],
        source_url=row["source_url"],
        last_updated=row["last_updated"],
        days_since_update=int(row["days_since_update"]),
    )


@lru_cache(maxsize=1)
def _load_all_companies() -> tuple[Company, ...]:
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    return tuple(_row_to_company(row) for row in rows)


def query_by_category(category: str) -> list[Company]:
    return [c for c in _load_all_companies() if c.category == category]
