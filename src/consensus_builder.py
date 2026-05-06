"""
Consensus Builder Module (Layer 4)

Handles strategic consensus logic:
- Trojan Horse filtering (betrayal_prob > BETRAYAL threshold)
- Poison Pill rejection (objection_weight > OBJECTION_CAP)
- Proposal selection based on viability score
- Supporter selection (non-objectors who aren't Trojan Horses)
"""


# Default thresholds (can be overridden via config)
DEFAULT_BETRAYAL_THRESHOLD = 0.3
DEFAULT_OBJECTION_CAP = 50


def filter_trojan_horses(representatives: list[dict], relations: list[dict],
                         betrayal_threshold: float = DEFAULT_BETRAYAL_THRESHOLD) -> set[str]:
    """
    Identify Trojan Horse representatives who should be excluded from supporters.

    A Trojan Horse is a rep whose *average* outgoing betrayal_prob exceeds the threshold.
    They look attractive (high influence) but are dangerously unreliable.

    Args:
        representatives: Cleaned reps list.
        relations: Cleaned relations list.
        betrayal_threshold: Maximum acceptable betrayal_prob (default 0.3).

    Returns:
        Set of rep IDs identified as Trojan Horses.
    """
    # Compute average outgoing betrayal_prob for each rep
    betrayal_sums = {}
    betrayal_counts = {}

    for rel in relations:
        from_id = rel["from"]
        prob = float(rel["betrayal_prob"])

        if from_id not in betrayal_sums:
            betrayal_sums[from_id] = 0.0
            betrayal_counts[from_id] = 0
        betrayal_sums[from_id] += prob
        betrayal_counts[from_id] += 1

    trojan_horses = set()
    for rep in representatives:
        rep_id = rep["id"]
        if rep_id in betrayal_sums and betrayal_counts[rep_id] > 0:
            avg_betrayal = betrayal_sums[rep_id] / betrayal_counts[rep_id]
            if avg_betrayal > betrayal_threshold:
                trojan_horses.add(rep_id)

    return trojan_horses


def filter_poison_pills(proposals: list[dict], objection_weights: dict[str, float],
                        objection_cap: float = DEFAULT_OBJECTION_CAP) -> list[dict]:
    """
    Filter out Poison Pill proposals — those with objection_weight exceeding the cap.

    A Poison Pill has high priority but faces overwhelming objections from
    influential reps, making it unviable to select.

    Args:
        proposals: Cleaned proposals list.
        objection_weights: Dict of proposal_id → aggregate objection weight.
        objection_cap: Maximum acceptable objection_weight (default 50).

    Returns:
        List of proposals that are NOT Poison Pills.
    """
    viable = []
    for prop in proposals:
        prop_id = prop["id"]
        weight = objection_weights.get(prop_id, 0.0)
        if weight <= objection_cap:
            viable.append(prop)
    return viable


def select_proposals(proposals: list[dict],
                     proposal_viability: dict[str, float]) -> list[str]:
    """
    Select proposals based on viability score (descending).

    All non-Poison-Pill proposals are included, sorted by viability.

    Args:
        proposals: Proposals that passed the Poison Pill filter.
        proposal_viability: Dict of proposal_id → viability score.

    Returns:
        List of selected proposal IDs, sorted by viability (highest first).
    """
    sorted_props = sorted(
        proposals,
        key=lambda p: proposal_viability.get(p["id"], 0),
        reverse=True,
    )
    return [p["id"] for p in sorted_props]


def select_supporters(representatives: list[dict], objections: list[dict],
                      selected_proposal_ids: list[str],
                      trojan_horses: set[str]) -> list[str]:
    """
    Select supporters for the agreement.

    A valid supporter must:
    1. NOT be a Trojan Horse (excluded by betrayal filter)
    2. NOT object to any of the selected proposals

    Args:
        representatives: Cleaned reps list.
        objections: Cleaned objections list.
        selected_proposal_ids: List of proposal IDs that were selected.
        trojan_horses: Set of rep IDs flagged as Trojan Horses.

    Returns:
        List of supporter rep IDs.
    """
    selected_set = set(selected_proposal_ids)

    # Build set of reps who object to any selected proposal
    objectors = set()
    for obj in objections:
        if obj["proposal_id"] in selected_set:
            objectors.add(obj["rep_id"])

    supporters = []
    for rep in representatives:
        rep_id = rep["id"]
        # Exclude Trojan Horses
        if rep_id in trojan_horses:
            continue
        # Exclude objectors to selected proposals
        if rep_id in objectors:
            continue
        supporters.append(rep_id)

    return supporters


def build_consensus(data: dict, features: dict,
                    betrayal_threshold: float = DEFAULT_BETRAYAL_THRESHOLD,
                    objection_cap: float = DEFAULT_OBJECTION_CAP) -> dict:
    """
    Build the consensus output with strategic filtering.

    Pipeline:
    1. Identify Trojan Horses
    2. Filter Poison Pill proposals
    3. Select proposals by viability
    4. Select supporters (non-objectors, non-Trojans)
    5. Ensure at least 1 proposal and 1 supporter

    Args:
        data: Cleaned data dict.
        features: Engineered features dict.
        betrayal_threshold: Trojan Horse threshold.
        objection_cap: Poison Pill objection weight cap.

    Returns:
        Dict with 'selected_proposals', 'supporters', 'trojan_horses'.
    """
    representatives = data["representatives"]
    proposals = data["proposals"]
    objections = data["objections"]
    relations = data["relations"]

    # Step 1: Identify Trojan Horses
    trojan_horses = filter_trojan_horses(representatives, relations, betrayal_threshold)

    # Step 2: Filter Poison Pill proposals
    viable_proposals = filter_poison_pills(
        proposals, features["objection_weights"], objection_cap
    )

    # Step 3: Select proposals by viability
    selected_proposal_ids = select_proposals(viable_proposals, features["proposal_viability"])

    # Step 4: Select supporters
    supporters = select_supporters(
        representatives, objections, selected_proposal_ids, trojan_horses
    )

    # Step 5: Ensure at least 1 proposal
    if not selected_proposal_ids and proposals:
        # If all proposals are Poison Pills, pick the one with lowest objection weight
        sorted_by_weight = sorted(
            proposals,
            key=lambda p: features["objection_weights"].get(p["id"], 0),
        )
        selected_proposal_ids = [sorted_by_weight[0]["id"]]
        # Recompute supporters with this fallback proposal
        supporters = select_supporters(
            representatives, objections, selected_proposal_ids, trojan_horses
        )

    # Step 6: Ensure at least 1 supporter
    if not supporters and representatives:
        # Pick the non-Trojan rep with fewest objections to selected proposals
        selected_set = set(selected_proposal_ids)
        rep_objection_counts = {}
        for rep in representatives:
            if rep["id"] not in trojan_horses:
                rep_objection_counts[rep["id"]] = 0

        # If all reps are Trojans, include everyone as candidates
        if not rep_objection_counts:
            for rep in representatives:
                rep_objection_counts[rep["id"]] = 0

        for obj in objections:
            if obj["proposal_id"] in selected_set:
                rid = obj["rep_id"]
                if rid in rep_objection_counts:
                    rep_objection_counts[rid] += 1

        best_rep = min(
            rep_objection_counts,
            key=lambda rid: (rep_objection_counts[rid],
                             -next(r["influence"] for r in representatives if r["id"] == rid)),
        )
        supporters = [best_rep]

    return {
        "selected_proposals": selected_proposal_ids,
        "supporters": supporters,
        "trojan_horses": trojan_horses,
    }
