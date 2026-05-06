"""
Tests for Phase 5: Alliance Detection
"""

import pytest
from src.alliance_detector import (
    UnionFind, detect_faction_infiltrators, detect_alliances,
    build_alliances,
)


class TestUnionFind:
    """Tests for the Union-Find data structure."""

    def test_single_union(self):
        uf = UnionFind()
        uf.union("a", "b")
        assert uf.find("a") == uf.find("b")

    def test_transitive_union(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("b", "c")
        assert uf.find("a") == uf.find("c")

    def test_separate_groups(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("c", "d")
        assert uf.find("a") != uf.find("c")

    def test_get_groups(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("c", "d")
        groups = uf.get_groups()
        assert len(groups) == 2
        assert sorted(["a", "b"]) in groups
        assert sorted(["c", "d"]) in groups

    def test_single_node_no_group(self):
        uf = UnionFind()
        uf.find("lonely")
        groups = uf.get_groups()
        assert len(groups) == 0  # Single nodes don't form a group


class TestDetectFactionInfiltrators:
    """Tests for faction infiltrator detection."""

    def test_high_faction_betrayal_flagged(self):
        """Rep with avg faction betrayal > 0.5 should be flagged."""
        reps = [{"id": "r1", "faction": "F1"}]
        avg = {"r1": 0.8}
        infiltrators = detect_faction_infiltrators(reps, avg, 0.5)
        assert "r1" in infiltrators

    def test_low_faction_betrayal_not_flagged(self):
        """Rep with avg faction betrayal <= 0.5 should NOT be flagged."""
        reps = [{"id": "r1", "faction": "F1"}]
        avg = {"r1": 0.2}
        infiltrators = detect_faction_infiltrators(reps, avg, 0.5)
        assert "r1" not in infiltrators

    def test_at_threshold_not_flagged(self):
        """Exactly at threshold should NOT be flagged (> not >=)."""
        reps = [{"id": "r1", "faction": "F1"}]
        avg = {"r1": 0.5}
        infiltrators = detect_faction_infiltrators(reps, avg, 0.5)
        assert "r1" not in infiltrators

    def test_no_faction_data(self):
        """Rep with no faction betrayal data defaults to 0."""
        reps = [{"id": "r1", "faction": "F1"}]
        avg = {}
        infiltrators = detect_faction_infiltrators(reps, avg, 0.5)
        assert len(infiltrators) == 0

    def test_classic_infiltrator_scenario(self):
        """Rep claims faction but betrays every member with prob > 0.5."""
        reps = [
            {"id": "spy", "faction": "Progressives"},
            {"id": "loyal1", "faction": "Progressives"},
            {"id": "loyal2", "faction": "Progressives"},
        ]
        avg = {"spy": 0.9, "loyal1": 0.05, "loyal2": 0.1}
        infiltrators = detect_faction_infiltrators(reps, avg, 0.5)
        assert "spy" in infiltrators
        assert "loyal1" not in infiltrators
        assert "loyal2" not in infiltrators


class TestDetectAlliances:
    """Tests for bidirectional alliance detection."""

    def test_bidirectional_strong_alliance(self):
        """Both A→B and B→A exceed thresholds → alliance."""
        scores = {
            ("r1", "r2"): 72.0,  # > 40
            ("r2", "r1"): 56.0,  # > 40
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 80},
            {"from": "r2", "to": "r1", "trust": 70},
        ]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert ["r1", "r2"] in alliances

    def test_unidirectional_no_alliance(self):
        """Only A→B strong but B→A weak → no alliance."""
        scores = {
            ("r1", "r2"): 72.0,  # > 40
            ("r2", "r1"): 20.0,  # < 40
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 80},
            {"from": "r2", "to": "r1", "trust": 30},
        ]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert len(alliances) == 0

    def test_false_friend_excluded(self):
        """Asymmetric trust: A trusts B (95) but B doesn't trust A (25)."""
        scores = {
            ("r1", "r2"): 85.0,  # high score
            ("r2", "r1"): 42.0,  # also above alliance_strength
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 95},  # > 60
            {"from": "r2", "to": "r1", "trust": 25},  # < 60 → False Friend!
        ]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert len(alliances) == 0

    def test_infiltrator_excluded(self):
        """Alliance pair where one is an infiltrator → excluded."""
        scores = {
            ("r1", "r2"): 72.0,
            ("r2", "r1"): 56.0,
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 80},
            {"from": "r2", "to": "r1", "trust": 70},
        ]
        infiltrators = {"r1"}
        alliances = detect_alliances(scores, rels, infiltrators, set(),
                                     alliance_strength=40, trust_threshold=60)
        assert len(alliances) == 0

    def test_trojan_excluded_from_alliances(self):
        """Alliance pair where one is a Trojan Horse → excluded."""
        scores = {
            ("r1", "r2"): 72.0,
            ("r2", "r1"): 56.0,
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 80},
            {"from": "r2", "to": "r1", "trust": 70},
        ]
        trojans = {"r2"}
        alliances = detect_alliances(scores, rels, set(), trojans,
                                     alliance_strength=40, trust_threshold=60)
        assert len(alliances) == 0

    def test_complete_rivalry(self):
        """All scores below threshold → empty alliances."""
        scores = {
            ("r1", "r2"): 10.0,
            ("r2", "r1"): 15.0,
            ("r1", "r3"): 5.0,
            ("r3", "r1"): 8.0,
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 20},
            {"from": "r2", "to": "r1", "trust": 25},
            {"from": "r1", "to": "r3", "trust": 10},
            {"from": "r3", "to": "r1", "trust": 15},
        ]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert alliances == []

    def test_empty_relations(self):
        """No relations at all → empty alliances."""
        alliances = detect_alliances({}, [], set(), set())
        assert alliances == []

    def test_multiple_alliances(self):
        """Multiple valid alliance pairs."""
        scores = {
            ("r1", "r2"): 72.0,
            ("r2", "r1"): 56.0,
            ("r3", "r4"): 80.0,
            ("r4", "r3"): 60.0,
        }
        rels = [
            {"from": "r1", "to": "r2", "trust": 80},
            {"from": "r2", "to": "r1", "trust": 70},
            {"from": "r3", "to": "r4", "trust": 90},
            {"from": "r4", "to": "r3", "trust": 75},
        ]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert ["r1", "r2"] in alliances
        assert ["r3", "r4"] in alliances

    def test_missing_reverse_direction(self):
        """Only A→B exists but no B→A → no alliance."""
        scores = {("r1", "r2"): 72.0}
        rels = [{"from": "r1", "to": "r2", "trust": 80}]
        alliances = detect_alliances(scores, rels, set(), set(),
                                     alliance_strength=40, trust_threshold=60)
        assert len(alliances) == 0


class TestBuildAlliances:
    """Integration tests for the full alliance pipeline."""

    def test_full_pipeline(self):
        """Full pipeline with infiltrator + alliances."""
        data = {
            "representatives": [
                {"id": "r1", "faction": "F1"},
                {"id": "r2", "faction": "F1"},
                {"id": "r3", "faction": "F2"},
                {"id": "spy", "faction": "F1"},
            ],
            "relations": [
                {"from": "r1", "to": "r2", "trust": 80, "betrayal_prob": 0.05},
                {"from": "r2", "to": "r1", "trust": 75, "betrayal_prob": 0.1},
                {"from": "spy", "to": "r1", "trust": 90, "betrayal_prob": 0.9},
                {"from": "spy", "to": "r2", "trust": 85, "betrayal_prob": 0.85},
            ],
        }
        features = {
            "relationship_scores": {
                ("r1", "r2"): 76.0,
                ("r2", "r1"): 67.5,
                ("spy", "r1"): 9.0,
                ("spy", "r2"): 12.75,
            },
            "faction_betrayal_avg": {
                "r1": 0.05,
                "r2": 0.1,
                "r3": 0.0,
                "spy": 0.875,
            },
        }
        result = build_alliances(data, features, trojan_horses=set(),
                                 faction_betrayal_threshold=0.5)
        assert "spy" in result["infiltrators"]
        assert ["r1", "r2"] in result["alliances"]

    def test_complete_rivalry_pipeline(self):
        """All reps are rivals → empty alliances."""
        data = {
            "representatives": [
                {"id": "r1", "faction": "F1"},
                {"id": "r2", "faction": "F2"},
            ],
            "relations": [
                {"from": "r1", "to": "r2", "trust": 10, "betrayal_prob": 0.9},
                {"from": "r2", "to": "r1", "trust": 15, "betrayal_prob": 0.8},
            ],
        }
        features = {
            "relationship_scores": {
                ("r1", "r2"): 1.0,
                ("r2", "r1"): 3.0,
            },
            "faction_betrayal_avg": {"r1": 0.0, "r2": 0.0},
        }
        result = build_alliances(data, features, trojan_horses=set())
        assert result["alliances"] == []
