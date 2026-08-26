from typing import Optional, TypedDict

from src.listicle_pipeline.state import RetrievalOutput


class CategoryCacheEntry(TypedDict):
    primary_keyword: str
    retrieval_output: Optional[RetrievalOutput]


# In-memory, single-process cache bridging primary_keyword/keyword_set across the
# classify -> retrieval -> generate-draft calls, since the contract's request shapes
# don't carry them forward. Appropriate for a single-operator internal tool; not built
# for multi-process or multi-tenant scale.
_cache: dict[str, CategoryCacheEntry] = {}


def set_primary_keyword(category_id: str, primary_keyword: str) -> None:
    entry = _cache.setdefault(category_id, {"primary_keyword": primary_keyword, "retrieval_output": None})
    entry["primary_keyword"] = primary_keyword


def set_retrieval_output(category_id: str, retrieval_output: RetrievalOutput) -> None:
    entry = _cache.setdefault(category_id, {"primary_keyword": retrieval_output.primary_keyword, "retrieval_output": None})
    entry["retrieval_output"] = retrieval_output


def get(category_id: str) -> Optional[CategoryCacheEntry]:
    return _cache.get(category_id)
