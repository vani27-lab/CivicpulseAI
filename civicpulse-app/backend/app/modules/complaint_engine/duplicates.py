"""Duplicate decision logic. Distance alone can NEVER confirm a duplicate."""
import math
from typing import List, Optional, Sequence, Tuple

from .config import Settings
from .constants import DUP_MERGED, DUP_NEW, DUP_POSSIBLE
from .domain import Candidate, DuplicateDecision, PossibleDuplicate


def cosine_similarity(a: Optional[Sequence[float]], b: Optional[Sequence[float]]) -> Optional[float]:
    """None when either vector is missing, empty, zero-norm, or the dimensions differ."""
    if not a or not b or len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return None
    return dot / (na * nb)


def best_similarity(new_embedding: Optional[Sequence[float]],
                    existing: Sequence[Sequence[float]]) -> Optional[float]:
    """Highest cosine similarity between the new image and any report already on the complaint."""
    sims = [s for s in (cosine_similarity(new_embedding, e) for e in existing) if s is not None]
    return max(sims) if sims else None


def decide_duplicate(scored: List[Tuple[Candidate, Optional[float]]], settings: Settings,
                     gps_accuracy: Optional[float]) -> DuplicateDecision:
    """
    scored: geographically eligible candidates (already same type/window/status) with their image
    similarity (None = could not be compared).
      - similarity >= merge threshold            -> MERGED (unless GPS too imprecise -> POSSIBLE)
      - similarity in [possible, merge)           -> POSSIBLE
      - similarity None (nothing to compare)      -> POSSIBLE (never confirmed on distance alone)
      - similarity < possible threshold           -> not a duplicate
    """
    if not scored:
        return DuplicateDecision(DUP_NEW)

    comparable = [(c, s) for c, s in scored if s is not None]
    best_c, best_s = max(comparable, key=lambda cs: cs[1]) if comparable else (None, None)

    low_accuracy = gps_accuracy is not None and gps_accuracy > settings.max_accuracy_for_auto_merge_m
    if best_c is not None and best_s >= settings.merge_similarity_threshold and not low_accuracy:
        return DuplicateDecision(DUP_MERGED, best_c.complaint_id, best_s)

    possible: List[PossibleDuplicate] = []
    for c, s in scored:
        if s is None:
            possible.append(PossibleDuplicate(c.complaint_id, None, "image similarity unavailable"))
        elif s >= settings.merge_similarity_threshold:  # only reachable when GPS accuracy blocked the merge
            possible.append(PossibleDuplicate(c.complaint_id, s, "high similarity but GPS accuracy too low to auto-merge"))
        elif s >= settings.possible_similarity_threshold:
            possible.append(PossibleDuplicate(c.complaint_id, s, "moderate image similarity"))
    possible.sort(key=lambda p: (p.similarity is None, -(p.similarity or 0)))
    if possible:
        return DuplicateDecision(DUP_POSSIBLE, None, best_s, possible)
    return DuplicateDecision(DUP_NEW, None, best_s)
