from typing import Any

from sqlalchemy import Subquery, func, select


def latest_per_group_subquery(group_col: Any, time_col: Any) -> Subquery:
    return (
        select(group_col.label("group_id"), func.max(time_col).label("latest"))
        .group_by(group_col)
        .subquery()
    )
