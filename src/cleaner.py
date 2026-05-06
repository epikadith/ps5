import statistics
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError


def _safe_numeric(value: Any, min_val: float = None, max_val: float = None,
                  default: float = None) -> float | None:
    """
    Attempt to cast a value to a float. Return None if it cannot be parsed.
    If min_val/max_val are provided, clamp the result.
    """
    if value is None:
        return default
    try:
        num = float(value)
    except (ValueError, TypeError):
        return default
    if min_val is not None and num < min_val:
        num = min_val
    if max_val is not None and num > max_val:
        num = max_val
    return num


class Representative(BaseModel):
    id: str
    name: str = ""
    faction: str = ""
    influence: Optional[float] = None

    model_config = {"extra": "allow"}

    @field_validator('influence', mode='before')
    @classmethod
    def parse_influence(cls, v: Any) -> Optional[float]:
        return _safe_numeric(v, min_val=0, max_val=100)


class Proposal(BaseModel):
    id: str
    title: str = ""
    sponsor: str = ""
    priority: float = 5.0

    model_config = {"extra": "allow"}

    @field_validator('priority', mode='before')
    @classmethod
    def parse_priority(cls, v: Any) -> float:
        res = _safe_numeric(v, min_val=1, max_val=10, default=5.0)
        return res if res is not None else 5.0


class Objection(BaseModel):
    rep_id: str = ""
    proposal_id: str = ""
    severity: float = 5.0

    model_config = {"extra": "allow"}

    @field_validator('severity', mode='before')
    @classmethod
    def parse_severity(cls, v: Any) -> float:
        res = _safe_numeric(v, min_val=1, max_val=10, default=5.0)
        return res if res is not None else 5.0


class Relation(BaseModel):
    from_id: str = Field(alias="from", default="")
    to_id: str = Field(alias="to", default="")
    trust: float = 0.0
    rivalry: float = 50.0
    betrayal_prob: float = 0.5

    model_config = {"extra": "allow", "populate_by_name": True}

    @field_validator('trust', mode='before')
    @classmethod
    def parse_trust(cls, v: Any) -> float:
        res = _safe_numeric(v, min_val=0, max_val=100, default=0.0)
        return res if res is not None else 0.0

    @field_validator('rivalry', mode='before')
    @classmethod
    def parse_rivalry(cls, v: Any) -> float:
        res = _safe_numeric(v, min_val=0, max_val=100, default=50.0)
        return res if res is not None else 50.0

    @field_validator('betrayal_prob', mode='before')
    @classmethod
    def parse_betrayal(cls, v: Any) -> float:
        res = _safe_numeric(v, min_val=0.0, max_val=1.0, default=0.5)
        return res if res is not None else 0.5


def clean_representatives(representatives: list[dict]) -> list[dict]:
    seen_ids = set()
    deduped = []
    valid_influences = []

    for rep_dict in representatives:
        if not rep_dict.get("id"):
            continue

        try:
            rep = Representative(**rep_dict)
        except ValidationError:
            continue

        if rep.id not in seen_ids:
            seen_ids.add(rep.id)
            if rep.influence is not None:
                valid_influences.append(rep.influence)
            deduped.append(rep.model_dump(by_alias=True))

    median_influence = statistics.median(valid_influences) if valid_influences else 50.0
    for rep in deduped:
        if rep["influence"] is None:
            rep["influence"] = median_influence

    return deduped


def clean_proposals(proposals: list[dict], valid_rep_ids: set[str]) -> list[dict]:
    seen_ids = set()
    cleaned = []

    for prop_dict in proposals:
        if not prop_dict.get("id"):
            continue

        try:
            prop = Proposal(**prop_dict)
        except ValidationError:
            continue

        if prop.id not in seen_ids:
            seen_ids.add(prop.id)
            if prop.sponsor in valid_rep_ids:
                cleaned.append(prop.model_dump(by_alias=True))

    return cleaned


def clean_objections(objections: list[dict], valid_rep_ids: set[str],
                     valid_proposal_ids: set[str]) -> list[dict]:
    seen_pairs = set()
    cleaned = []

    for obj_dict in objections:
        try:
            obj = Objection(**obj_dict)
        except ValidationError:
            continue

        if obj.rep_id not in valid_rep_ids or obj.proposal_id not in valid_proposal_ids:
            continue

        pair = (obj.rep_id, obj.proposal_id)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            cleaned.append(obj.model_dump(by_alias=True))

    return cleaned


def clean_relations(relations: list[dict], valid_rep_ids: set[str]) -> list[dict]:
    seen_pairs = set()
    cleaned = []

    for rel_dict in relations:
        try:
            rel = Relation(**rel_dict)
        except ValidationError:
            continue

        if rel.from_id not in valid_rep_ids or rel.to_id not in valid_rep_ids:
            continue

        if rel.from_id == rel.to_id:
            continue

        pair = (rel.from_id, rel.to_id)
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            cleaned.append(rel.model_dump(by_alias=True))

    return cleaned


def clean_all_data(data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    representatives = clean_representatives(data["representatives"])
    valid_rep_ids = {rep["id"] for rep in representatives}

    proposals = clean_proposals(data["proposals"], valid_rep_ids)
    valid_proposal_ids = {prop["id"] for prop in proposals}

    objections = clean_objections(data["objections"], valid_rep_ids, valid_proposal_ids)
    relations = clean_relations(data["relations"], valid_rep_ids)

    return {
        "representatives": representatives,
        "proposals": proposals,
        "objections": objections,
        "relations": relations,
    }
