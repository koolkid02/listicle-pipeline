from src.listicle_pipeline import db
from src.listicle_pipeline.state import CATEGORIES, Company

EXPECTED_COUNTS = {
    "Project Management Software": 18,
    "Hiring and HR Software": 17,
    "Event Registration and Ticketing Software": 17,
    "End-to-End CRM Software": 17,
    "Tax Filing Software": 17,
    "Email Marketing Software": 17,
}


def test_all_categories_resolve():
    for category in CATEGORIES:
        companies = db.query_by_category(category)
        assert len(companies) == EXPECTED_COUNTS[category]
        assert all(isinstance(c, Company) for c in companies)
        assert all(c.category == category for c in companies)


def test_company_fields_populated():
    companies = db.query_by_category("Project Management Software")
    first = companies[0]
    assert first.company_name
    assert first.what_it_does_well
    assert 1 <= len(first.what_it_does_well) <= 5
    assert 1 <= len(first.gaps) <= 2
    assert first.website_url.startswith("http")


def test_unknown_category_returns_empty():
    assert db.query_by_category("Not A Real Category") == []
