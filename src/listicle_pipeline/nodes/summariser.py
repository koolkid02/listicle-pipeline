from datetime import datetime, timezone

from pydantic import BaseModel

from ..config import TEMPERATURE_SUMMARISER, get_llm, load_prompt
from ..state import Company, CompanySummary, SummarySource


class _SummariseCompanyInput(BaseModel):
    company: Company
    primary_keyword: str


class _SummaryProse(BaseModel):
    summary_blurb: str
    does_well_prose: list[str]
    gaps_prose: list[str]
    best_for_line: str


def summarise_company(raw: dict) -> dict:
    parsed = _SummariseCompanyInput.model_validate(raw)
    company = parsed.company

    llm = get_llm(TEMPERATURE_SUMMARISER).with_structured_output(_SummaryProse)
    prompt = load_prompt("summariser_company").format(
        primary_keyword=parsed.primary_keyword,
        category=company.category,
        company_name=company.company_name,
        positioning=company.positioning,
        starting_price=company.starting_price,
        aggregated_rating=company.aggregated_rating,
        review_count=company.review_count,
        what_it_does_well="; ".join(company.what_it_does_well),
        gaps="; ".join(company.gaps),
        best_for=company.best_for,
    )
    prose: _SummaryProse = llm.invoke(prompt)

    summary = CompanySummary(
        company_name=company.company_name,
        summary_blurb=prose.summary_blurb,
        does_well_prose=prose.does_well_prose,
        gaps_prose=prose.gaps_prose,
        best_for_line=prose.best_for_line,
        pricing_line=f"From {company.starting_price}",
        rating_line=f"G2: {company.aggregated_rating}/5",
        source=SummarySource(
            company_name=company.company_name,
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
    return {"company_summaries": [summary]}
