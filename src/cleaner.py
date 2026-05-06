"""
Cleaner Module (Layer 1)

Handles data cleaning operations:
- Type casting for dirty attributes (string "85" → int 85)
- Null value handling (median imputation for influence)
- Range clamping (150 → 100)
- Deduplication (by normalized ID, keep first)
- Ghost reference filtering
- Dirty CSV row handling (non-numeric trust/rivalry/betrayal_prob)
"""

import statistics
from typing import Any


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


def clean_representatives(representatives: list[dict]) -> list[dict]:
    """
    Clean representatives data:
    1. Cast influence to numeric
    2. Clamp influence to [0, 100]
    3. Impute null influence with median of valid values
    4. Deduplicate by normalized ID (keep first occurrence)
    """
    # Step 1: Deduplicate by ID, keeping first occurrence
    seen_ids = set()
    deduped = []
    for rep in representatives:
        rep_id = rep.get("id", "")
        if rep_id and rep_id not in seen_ids:
            seen_ids.add(rep_id)
            deduped.append(rep)

    # Step 2: Cast influence to numeric, clamp to [0, 100], track valid values
    valid_influences = []
    for rep in deduped:
        raw_influence = rep.get("influence")
        parsed = _safe_numeric(raw_influence, min_val=0, max_val=100)
        rep["influence"] = parsed
        if parsed is not None:
            valid_influences.append(parsed)

    # Step 3: Impute null influence with median
    if valid_influences:
        median_influence = statistics.median(valid_influences)
    else:
        median_influence = 50  # Fallback default

    for rep in deduped:
        if rep["influence"] is None:
            rep["influence"] = median_influence

    return deduped


def clean_proposals(proposals: list[dict], valid_rep_ids: set[str]) -> list[dict]:
    """
    Clean proposals data:
    1. Cast priority to numeric, clamp to [1, 10]
    2. Deduplicate by ID (keep first occurrence)
    3. Filter out proposals with ghost sponsors (sponsors not in valid_rep_ids)
    """
    # Step 1: Deduplicate by ID, keeping first occurrence
    seen_ids = set()
    deduped = []
    for prop in proposals:
        prop_id = prop.get("id", "")
        if prop_id and prop_id not in seen_ids:
            seen_ids.add(prop_id)
            deduped.append(prop)

    # Step 2: Cast priority to numeric, clamp to [1, 10]
    for prop in deduped:
        raw_priority = prop.get("priority")
        parsed = _safe_numeric(raw_priority, min_val=1, max_val=10, default=5)
        prop["priority"] = parsed

    # Step 3: Filter out proposals with ghost sponsors
    cleaned = []
    for prop in deduped:
        sponsor = prop.get("sponsor", "")
        if sponsor in valid_rep_ids:
            cleaned.append(prop)

    return cleaned


def clean_objections(objections: list[dict], valid_rep_ids: set[str],
                     valid_proposal_ids: set[str]) -> list[dict]:
    """
    Clean objections data:
    1. Cast severity to numeric, clamp to [1, 10]
    2. Filter ghost references (rep_id or proposal_id not in valid sets)
    3. Deduplicate by (rep_id, proposal_id) pair - keep first occurrence
    """
    cleaned = []
    seen_pairs = set()

    for obj in objections:
        rep_id = obj.get("rep_id", "")
        proposal_id = obj.get("proposal_id", "")

        # Filter ghost references
        if rep_id not in valid_rep_ids:
            continue
        if proposal_id not in valid_proposal_ids:
            continue

        # Deduplicate by (rep_id, proposal_id) pair
        pair_key = (rep_id, proposal_id)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        # Cast severity to numeric, clamp to [1, 10]
        raw_severity = obj.get("severity")
        parsed = _safe_numeric(raw_severity, min_val=1, max_val=10)
        if parsed is None:
            # If severity is completely invalid, use median severity (5)
            parsed = 5.0
        obj["severity"] = parsed
        cleaned.append(obj)

    return cleaned


def clean_relations(relations: list[dict], valid_rep_ids: set[str]) -> list[dict]:
    """
    Clean relations data:
    1. Cast trust, rivalry, betrayal_prob to numeric with appropriate ranges
    2. Filter ghost references (from/to not in valid_rep_ids)
    3. Handle dirty CSV rows (non-numeric values)
    4. Deduplicate by (from, to) pair - keep first occurrence
    5. Clamp values: trust [0,100], rivalry [0,100], betrayal_prob [0.0, 1.0]
    """
    cleaned = []
    seen_pairs = set()

    for rel in relations:
        from_id = rel.get("from", "")
        to_id = rel.get("to", "")

        # Filter ghost references
        if from_id not in valid_rep_ids or to_id not in valid_rep_ids:
            continue

        # Skip self-relations
        if from_id == to_id:
            continue

        # Deduplicate by (from, to) pair
        pair_key = (from_id, to_id)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        # Cast and clamp trust [0, 100]
        raw_trust = rel.get("trust")
        trust = _safe_numeric(raw_trust, min_val=0, max_val=100)
        if trust is None:
            trust = 0.0  # Default: no trust if missing
        rel["trust"] = trust

        # Cast and clamp rivalry [0, 100]
        raw_rivalry = rel.get("rivalry")
        rivalry = _safe_numeric(raw_rivalry, min_val=0, max_val=100)
        if rivalry is None:
            rivalry = 50.0  # Default: moderate rivalry if missing
        rel["rivalry"] = rivalry

        # Cast and clamp betrayal_prob [0.0, 1.0]
        raw_betrayal = rel.get("betrayal_prob")
        betrayal_prob = _safe_numeric(raw_betrayal, min_val=0.0, max_val=1.0)
        if betrayal_prob is None:
            betrayal_prob = 0.5  # Default: uncertain if missing
        rel["betrayal_prob"] = betrayal_prob

        cleaned.append(rel)

    return cleaned


def clean_all_data(data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    Run the full cleaning pipeline on all datasets.

    Processing order matters:
    1. Clean representatives first (to get valid rep IDs)
    2. Clean proposals (needs valid rep IDs for ghost sponsor filtering)
    3. Clean objections (needs valid rep IDs and proposal IDs)
    4. Clean relations (needs valid rep IDs)
    """
    # Step 1: Clean representatives
    representatives = clean_representatives(data["representatives"])
    valid_rep_ids = {rep["id"] for rep in representatives}

    # Step 2: Clean proposals (filter ghost sponsors)
    proposals = clean_proposals(data["proposals"], valid_rep_ids)
    valid_proposal_ids = {prop["id"] for prop in proposals}

    # Step 3: Clean objections (filter ghost references)
    objections = clean_objections(data["objections"], valid_rep_ids, valid_proposal_ids)

    # Step 4: Clean relations (filter ghost references, handle dirty CSV)
    relations = clean_relations(data["relations"], valid_rep_ids)

    return {
        "representatives": representatives,
        "proposals": proposals,
        "objections": objections,
        "relations": relations,
    }
