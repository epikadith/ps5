"""
Feature Engineering Module (Layer 2)

Derives meaningful features from cleaned data:
- relationship_score = trust * (1 - betrayal_prob)
- objection_weight = sum(severity * objector_influence) per proposal
- proposal_viability = priority * (1 - normalized_controversy)
- faction_betrayal_avg per rep (average betrayal_prob toward same-faction members)
"""


def compute_relationship_scores(relations: list[dict]) -> dict[tuple[str, str], float]:
    """
    Compute relationship_score for each directed (from, to) pair.

    Formula: relationship_score = trust * (1 - betrayal_prob)

    A rep with trust=90 but betrayal_prob=0.9 scores 90 * 0.1 = 9 (dangerous).
    A rep with trust=90 but betrayal_prob=0.05 scores 90 * 0.95 = 85.5 (reliable).

    Returns:
        Dictionary mapping (from_id, to_id) → relationship_score
    """
    scores = {}
    for rel in relations:
        from_id = rel["from"]
        to_id = rel["to"]
        trust = float(rel["trust"])
        betrayal_prob = float(rel["betrayal_prob"])
        score = trust * (1 - betrayal_prob)
        scores[(from_id, to_id)] = score
    return scores


def compute_objection_weights(objections: list[dict],
                              representatives: list[dict]) -> dict[str, float]:
    """
    Compute objection_weight for each proposal.

    Formula: objection_weight = sum(severity * objector_influence)

    A powerful rep's objection carries more weight than a weak one.

    Returns:
        Dictionary mapping proposal_id → aggregate objection_weight
    """
    # Build rep influence lookup
    rep_influence = {}
    for rep in representatives:
        rep_influence[rep["id"]] = float(rep["influence"])

    # Aggregate objection weights per proposal
    weights = {}
    for obj in objections:
        proposal_id = obj["proposal_id"]
        rep_id = obj["rep_id"]
        severity = float(obj["severity"])
        influence = rep_influence.get(rep_id, 0)

        weight = severity * influence
        if proposal_id not in weights:
            weights[proposal_id] = 0.0
        weights[proposal_id] += weight

    return weights


def compute_proposal_viability(proposals: list[dict],
                               objection_weights: dict[str, float]) -> dict[str, float]:
    """
    Compute proposal_viability for each proposal.

    Formula: proposal_viability = priority * (1 - normalized_controversy)

    Where normalized_controversy = objection_weight / max_objection_weight
    (normalized to [0, 1] range).

    If no proposal has objections, all controversies are 0.

    Returns:
        Dictionary mapping proposal_id → viability score
    """
    # Find max objection weight for normalization
    if objection_weights:
        max_weight = max(objection_weights.values())
    else:
        max_weight = 0.0

    viability = {}
    for prop in proposals:
        prop_id = prop["id"]
        priority = float(prop["priority"])
        raw_weight = objection_weights.get(prop_id, 0.0)

        if max_weight > 0:
            normalized_controversy = raw_weight / max_weight
        else:
            normalized_controversy = 0.0

        viability[prop_id] = priority * (1 - normalized_controversy)

    return viability


def compute_faction_betrayal_avg(representatives: list[dict],
                                 relations: list[dict]) -> dict[str, float]:
    """
    Compute the average betrayal_prob of each rep toward members of their own faction.

    This is used to detect faction infiltrators: a rep who claims a faction
    but betrays its members with high probability.

    Returns:
        Dictionary mapping rep_id → average betrayal_prob toward same-faction members.
        Reps with no same-faction relations get a value of 0.0.
    """
    # Build faction lookup
    rep_factions = {}
    for rep in representatives:
        rep_factions[rep["id"]] = rep.get("faction", "")

    # Accumulate betrayal probs toward same-faction members
    betrayal_sums = {}  # rep_id → list of betrayal_probs toward same-faction
    for rel in relations:
        from_id = rel["from"]
        to_id = rel["to"]
        betrayal_prob = float(rel["betrayal_prob"])

        from_faction = rep_factions.get(from_id, "")
        to_faction = rep_factions.get(to_id, "")

        # Only count if same faction and faction is non-empty
        if from_faction and from_faction == to_faction:
            if from_id not in betrayal_sums:
                betrayal_sums[from_id] = []
            betrayal_sums[from_id].append(betrayal_prob)

    # Compute averages
    faction_betrayal_avg = {}
    for rep in representatives:
        rep_id = rep["id"]
        probs = betrayal_sums.get(rep_id, [])
        if probs:
            faction_betrayal_avg[rep_id] = sum(probs) / len(probs)
        else:
            faction_betrayal_avg[rep_id] = 0.0

    return faction_betrayal_avg


def engineer_features(data: dict[str, list[dict]]) -> dict:
    """
    Run the full feature engineering pipeline.

    Args:
        data: Cleaned data dict with 'representatives', 'proposals', 'objections', 'relations'.

    Returns:
        Dictionary with all computed features:
        - 'relationship_scores': dict[(from, to)] → score
        - 'objection_weights': dict[proposal_id] → weight
        - 'proposal_viability': dict[proposal_id] → viability
        - 'faction_betrayal_avg': dict[rep_id] → avg betrayal toward own faction
    """
    relationship_scores = compute_relationship_scores(data["relations"])
    objection_weights = compute_objection_weights(data["objections"], data["representatives"])
    proposal_viability = compute_proposal_viability(data["proposals"], objection_weights)
    faction_betrayal_avg = compute_faction_betrayal_avg(
        data["representatives"], data["relations"]
    )

    return {
        "relationship_scores": relationship_scores,
        "objection_weights": objection_weights,
        "proposal_viability": proposal_viability,
        "faction_betrayal_avg": faction_betrayal_avg,
    }
