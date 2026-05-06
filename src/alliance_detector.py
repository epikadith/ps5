"""
Alliance Detector Module (Layer 4)

Handles alliance detection:
- Bidirectional alliance detection (both directions exceed ALLIANCE_STRENGTH)
- False Friend detection (asymmetric trust — requires bidirectional trust > TRUST)
- Faction infiltrator flagging (rep betrays faction members with prob > FACTION_BETRAYAL)
- Complete rivalry handling (return empty alliances)
- Union-Find data structure for connected components
"""


# Default thresholds
DEFAULT_ALLIANCE_STRENGTH = 40
DEFAULT_TRUST_THRESHOLD = 60
DEFAULT_FACTION_BETRAYAL_THRESHOLD = 0.5


class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure for tracking connected components.
    Used to group allied representatives into alliance clusters.
    """

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x: str) -> str:
        """Find the root of element x with path compression."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        """Unite the sets containing x and y using union by rank."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def get_groups(self) -> list[list[str]]:
        """Return all connected components as sorted lists of members."""
        groups = {}
        for node in self.parent:
            root = self.find(node)
            if root not in groups:
                groups[root] = []
            groups[root].append(node)
        # Only return groups with 2+ members, sorted
        return [sorted(members) for members in groups.values() if len(members) >= 2]


def detect_faction_infiltrators(representatives: list[dict],
                                faction_betrayal_avg: dict[str, float],
                                faction_betrayal_threshold: float = DEFAULT_FACTION_BETRAYAL_THRESHOLD
                                ) -> set[str]:
    """
    Detect faction infiltrators: reps who claim a faction but betray its members.

    A rep is an infiltrator if their average betrayal_prob toward same-faction
    members exceeds the threshold.

    Args:
        representatives: Cleaned reps list.
        faction_betrayal_avg: Dict of rep_id → avg betrayal toward own faction.
        faction_betrayal_threshold: Threshold for infiltrator detection (default 0.5).

    Returns:
        Set of rep IDs identified as faction infiltrators.
    """
    infiltrators = set()
    for rep in representatives:
        rep_id = rep["id"]
        avg_betrayal = faction_betrayal_avg.get(rep_id, 0.0)
        if avg_betrayal > faction_betrayal_threshold:
            infiltrators.add(rep_id)
    return infiltrators


def detect_alliances(relationship_scores: dict[tuple[str, str], float],
                     relations: list[dict],
                     infiltrators: set[str],
                     trojan_horses: set[str],
                     alliance_strength: float = DEFAULT_ALLIANCE_STRENGTH,
                     trust_threshold: float = DEFAULT_TRUST_THRESHOLD
                     ) -> list[list[str]]:
    """
    Detect bidirectional alliances between representatives.

    An alliance between A and B requires:
    1. Bidirectional relationship_score: both A→B and B→A exceed ALLIANCE_STRENGTH
    2. Bidirectional trust: both A→B and B→A trust > TRUST_THRESHOLD (False Friend filter)
    3. Neither A nor B is a faction infiltrator
    4. Neither A nor B is a Trojan Horse

    If all relationship_scores are below thresholds (complete rivalry), returns [].

    Args:
        relationship_scores: Dict of (from, to) → relationship_score.
        relations: Cleaned relations list (for trust lookup).
        infiltrators: Set of faction infiltrator rep IDs.
        trojan_horses: Set of Trojan Horse rep IDs.
        alliance_strength: Min relationship_score for alliance (default 40).
        trust_threshold: Min bidirectional trust for alliance (default 60).

    Returns:
        List of alliance pairs [rep_a, rep_b], sorted.
    """
    # Build trust lookup
    trust_lookup = {}
    for rel in relations:
        trust_lookup[(rel["from"], rel["to"])] = float(rel["trust"])

    # Excluded reps: infiltrators and Trojan Horses
    excluded = infiltrators | trojan_horses

    # Collect all unique rep IDs from relationship scores
    all_reps = set()
    for (from_id, to_id) in relationship_scores:
        all_reps.add(from_id)
        all_reps.add(to_id)

    # Find bidirectional alliance pairs
    uf = UnionFind()
    alliance_pairs = []

    checked = set()
    for (from_id, to_id), score_ab in relationship_scores.items():
        # Skip if either is excluded
        if from_id in excluded or to_id in excluded:
            continue

        # Avoid double-checking
        pair = tuple(sorted([from_id, to_id]))
        if pair in checked:
            continue
        checked.add(pair)

        # Check bidirectional relationship_score
        score_ba = relationship_scores.get((to_id, from_id), 0.0)
        if score_ab < alliance_strength or score_ba < alliance_strength:
            continue

        # Check bidirectional trust (False Friend filter)
        trust_ab = trust_lookup.get((from_id, to_id), 0.0)
        trust_ba = trust_lookup.get((to_id, from_id), 0.0)
        if trust_ab < trust_threshold or trust_ba < trust_threshold:
            continue

        # Valid bidirectional alliance
        alliance_pairs.append(sorted([from_id, to_id]))
        uf.union(from_id, to_id)

    # Return alliance pairs sorted for deterministic output
    alliance_pairs.sort()
    return alliance_pairs


def build_alliances(data: dict, features: dict, trojan_horses: set[str],
                    alliance_strength: float = DEFAULT_ALLIANCE_STRENGTH,
                    trust_threshold: float = DEFAULT_TRUST_THRESHOLD,
                    faction_betrayal_threshold: float = DEFAULT_FACTION_BETRAYAL_THRESHOLD
                    ) -> dict:
    """
    Full alliance detection pipeline.

    1. Detect faction infiltrators
    2. Detect bidirectional alliances (excluding infiltrators and Trojans)
    3. Handle complete rivalry (empty alliances)

    Args:
        data: Cleaned data dict.
        features: Engineered features dict.
        trojan_horses: Set of Trojan Horse rep IDs from consensus builder.
        alliance_strength: Min relationship_score for alliance.
        trust_threshold: Min bidirectional trust for alliance.
        faction_betrayal_threshold: Threshold for infiltrator detection.

    Returns:
        Dict with 'alliances' (list of pairs) and 'infiltrators' (set of rep IDs).
    """
    # Step 1: Detect faction infiltrators
    infiltrators = detect_faction_infiltrators(
        data["representatives"],
        features["faction_betrayal_avg"],
        faction_betrayal_threshold,
    )

    # Step 2: Detect alliances
    alliances = detect_alliances(
        features["relationship_scores"],
        data["relations"],
        infiltrators,
        trojan_horses,
        alliance_strength,
        trust_threshold,
    )

    return {
        "alliances": alliances,
        "infiltrators": infiltrators,
    }
