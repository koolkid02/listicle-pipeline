"""Structural groundedness checks - no LLM-as-judge, no extra API calls.

Each check enforces a constraint the corresponding prompt already states explicitly
(see src/listicle_pipeline/prompts/*.txt), so these are regression tests on whether the
model honors its own documented contract, not a fuzzy semantic judgment:

- summariser_company.txt: "do not invent anything beyond [the given facts]" / "Do not
  mention pricing or star rating in any of these fields"
- formatter_buying_criteria.txt: "generic to the category (don't reference any specific
  company)"
- formatter_faq.txt: "generic to the category (don't invent facts about specific
  companies)"
"""

import re

from src.listicle_pipeline.state import BuyingCriterionItem, Company, CompanySummary, FaqItem, TitleDekBlock

_PRICE_RE = re.compile(r"\$\s?\d")
_RATING_RE = re.compile(r"\b\d(\.\d)?\s*/\s*5\b")
_LEADING_NUMBER_RE = re.compile(r"^\D*(\d+)")


class GroundednessResult:
    def __init__(self, violations: list[str]):
        self.violations = violations

    @property
    def ok(self) -> bool:
        return not self.violations

    def __repr__(self) -> str:
        return f"GroundednessResult(ok={self.ok}, violations={self.violations})"


def check_summary_groundedness(company: Company, summary: CompanySummary) -> GroundednessResult:
    violations = []

    if len(summary.does_well_prose) != len(company.what_it_does_well):
        violations.append(
            f"does_well_prose has {len(summary.does_well_prose)} items, "
            f"source had {len(company.what_it_does_well)}"
        )
    if len(summary.gaps_prose) != len(company.gaps):
        violations.append(
            f"gaps_prose has {len(summary.gaps_prose)} items, source had {len(company.gaps)}"
        )

    prose_fields = {
        "summary_blurb": summary.summary_blurb,
        "does_well_prose": " ".join(summary.does_well_prose),
        "gaps_prose": " ".join(summary.gaps_prose),
        "best_for_line": summary.best_for_line,
    }
    for field_name, text in prose_fields.items():
        if _PRICE_RE.search(text):
            violations.append(f"{field_name} mentions pricing, which the prompt forbids: {text!r}")
        if _RATING_RE.search(text):
            violations.append(f"{field_name} mentions a star rating, which the prompt forbids: {text!r}")

    return GroundednessResult(violations)


def check_no_company_names(text: str, all_company_names: list[str]) -> GroundednessResult:
    """For sections whose prompt explicitly says to stay generic (buying criteria, FAQ) -
    flag any real company name (from the full DB, not just the approved set) leaking in."""
    violations = [name for name in all_company_names if name in text]
    return GroundednessResult(
        [f"mentions specific company '{name}', which the prompt requires staying generic about" for name in violations]
    )


def check_buying_criteria_groundedness(items: list[BuyingCriterionItem], all_company_names: list[str]) -> GroundednessResult:
    text = " ".join(f"{item.h3} {item.body}" for item in items)
    return check_no_company_names(text, all_company_names)


def check_faq_groundedness(items: list[FaqItem], all_company_names: list[str]) -> GroundednessResult:
    text = " ".join(f"{item.question} {item.answer}" for item in items)
    return check_no_company_names(text, all_company_names)


def check_title_dek_company_count(block: TitleDekBlock, company_count: int) -> GroundednessResult:
    """The prompt asks for the title to state the actual company_count, e.g.
    '8 Best ... Platforms in 2026' for company_count=8 - check the number matches."""
    match = _LEADING_NUMBER_RE.match(block.title)
    if match is None:
        return GroundednessResult([f"title has no leading count: {block.title!r}"])
    stated = int(match.group(1))
    if stated != company_count:
        return GroundednessResult(
            [f"title states {stated} companies but {company_count} were approved: {block.title!r}"]
        )
    return GroundednessResult([])
