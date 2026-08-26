from src.listicle_pipeline.state import CATEGORIES

CATEGORY_ID_MAP: dict[str, str] = {
    "project-management": "Project Management Software",
    "hiring-hr": "Hiring and HR Software",
    "event-registration-ticketing": "Event Registration and Ticketing Software",
    "crm": "End-to-End CRM Software",
    "tax-filing": "Tax Filing Software",
    "email-marketing": "Email Marketing Software",
}

assert set(CATEGORY_ID_MAP.values()) == set(CATEGORIES)

CATEGORY_NAME_TO_ID: dict[str, str] = {name: id_ for id_, name in CATEGORY_ID_MAP.items()}


def available_categories() -> list[dict[str, str]]:
    return [{"id": id_, "name": name} for id_, name in CATEGORY_ID_MAP.items()]
