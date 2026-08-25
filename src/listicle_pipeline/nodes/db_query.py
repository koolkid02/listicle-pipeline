from .. import db
from ..state import PipelineState


def tools_db_query(state: PipelineState) -> dict:
    return {"db_companies": db.query_by_category(state.category)}
