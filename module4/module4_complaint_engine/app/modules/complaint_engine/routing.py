"""Category -> department routing (names resolved against the existing departments table)."""
from typing import Callable, Optional, Tuple
from uuid import UUID

from .config import Settings


def department_name_for(issue_type: str, settings: Settings) -> str:
    return settings.department_map.get(issue_type, settings.department_map.get("unclassified", "Manual review"))


def resolve_department(issue_type: str, settings: Settings,
                       lookup: Callable[[str], Optional[UUID]]) -> Tuple[Optional[UUID], str, Optional[str]]:
    """Returns (department_id, department_name, warning). Never creates departments."""
    name = department_name_for(issue_type, settings)
    dept_id = lookup(name)
    if dept_id is None:
        return None, name, f"department_not_found:{name}"
    return dept_id, name, None
