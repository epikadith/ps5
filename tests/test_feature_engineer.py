"""
Tests for Phase 3: Feature Engineering
"""

import pytest
from src.feature_engineer import (
    compute_relationship_scores, compute_objection_weights,
    compute_proposal_viability, compute_faction_betrayal_avg,
    engineer_features,
)


class TestRelationshipScores:
    def test_basic_computation(self):
        rels = [{"from": "r1", "to": "r2", "trust": 80, "betrayal_prob": 0.1}]
        scores = compute_relationship_scores(rels)
        assert scores[("r1", "r2")] == pytest.approx(72.0)

    def test_high_trust_high_betrayal(self):
        """trust=90, betrayal=0.9 → 90*0.1 = 9.0 (dangerous)"""
        rels = [{"from": "r1", "to": "r2", "trust": 90, "betrayal_prob": 0.9}]
        scores = compute_relationship_scores(rels)
        assert scores[("r1", "r2")] == pytest.approx(9.0)

    def test_high_trust_low_betrayal(self):
        """trust=90, betrayal=0.05 → 90*0.95 = 85.5 (reliable)"""
        rels = [{"from": "r1", "to": "r2", "trust": 90, "betrayal_prob": 0.05}]
        scores = compute_relationship_scores(rels)
        assert scores[("r1", "r2")] == pytest.approx(85.5)

    def test_zero_trust(self):
        rels = [{"from": "r1", "to": "r2", "trust": 0, "betrayal_prob": 0.1}]
        scores = compute_relationship_scores(rels)
        assert scores[("r1", "r2")] == pytest.approx(0.0)

    def test_zero_betrayal(self):
        rels = [{"from": "r1", "to": "r2", "trust": 80, "betrayal_prob": 0.0}]
        scores = compute_relationship_scores(rels)
        assert scores[("r1", "r2")] == pytest.approx(80.0)

    def test_multiple_pairs(self):
        rels = [
            {"from": "r1", "to": "r2", "trust": 80, "betrayal_prob": 0.1},
            {"from": "r2", "to": "r1", "trust": 60, "betrayal_prob": 0.3},
        ]
        scores = compute_relationship_scores(rels)
        assert len(scores) == 2
        assert scores[("r1", "r2")] == pytest.approx(72.0)
        assert scores[("r2", "r1")] == pytest.approx(42.0)

    def test_empty_relations(self):
        scores = compute_relationship_scores([])
        assert scores == {}


class TestObjectionWeights:
    def test_basic_computation(self):
        objs = [{"rep_id": "r1", "proposal_id": "p1", "severity": 8}]
        reps = [{"id": "r1", "influence": 90}]
        weights = compute_objection_weights(objs, reps)
        assert weights["p1"] == pytest.approx(720.0)

    def test_multiple_objections_aggregate(self):
        objs = [
            {"rep_id": "r1", "proposal_id": "p1", "severity": 8},
            {"rep_id": "r2", "proposal_id": "p1", "severity": 5},
        ]
        reps = [
            {"id": "r1", "influence": 90},
            {"id": "r2", "influence": 70},
        ]
        weights = compute_objection_weights(objs, reps)
        assert weights["p1"] == pytest.approx(720.0 + 350.0)

    def test_no_objections(self):
        weights = compute_objection_weights([], [{"id": "r1", "influence": 90}])
        assert weights == {}

    def test_unknown_rep_uses_zero(self):
        objs = [{"rep_id": "r_unknown", "proposal_id": "p1", "severity": 8}]
        reps = [{"id": "r1", "influence": 90}]
        weights = compute_objection_weights(objs, reps)
        assert weights["p1"] == pytest.approx(0.0)


class TestProposalViability:
    def test_no_objections_full_viability(self):
        props = [{"id": "p1", "priority": 8}]
        viability = compute_proposal_viability(props, {})
        assert viability["p1"] == pytest.approx(8.0)

    def test_max_objection_zero_viability(self):
        """Proposal with max objection weight → viability = priority * 0 = 0."""
        props = [{"id": "p1", "priority": 10}]
        weights = {"p1": 500.0}
        viability = compute_proposal_viability(props, weights)
        assert viability["p1"] == pytest.approx(0.0)

    def test_partial_objection(self):
        props = [
            {"id": "p1", "priority": 10},
            {"id": "p2", "priority": 8},
        ]
        weights = {"p1": 100.0, "p2": 50.0}
        viability = compute_proposal_viability(props, weights)
        # p1: 10 * (1 - 100/100) = 0
        # p2: 8 * (1 - 50/100) = 4
        assert viability["p1"] == pytest.approx(0.0)
        assert viability["p2"] == pytest.approx(4.0)

    def test_no_proposals(self):
        viability = compute_proposal_viability([], {"p1": 100})
        assert viability == {}


class TestFactionBetrayalAvg:
    def test_same_faction_betrayal(self):
        reps = [
            {"id": "r1", "faction": "F1"},
            {"id": "r2", "faction": "F1"},
        ]
        rels = [{"from": "r1", "to": "r2", "betrayal_prob": 0.8}]
        avg = compute_faction_betrayal_avg(reps, rels)
        assert avg["r1"] == pytest.approx(0.8)
        assert avg["r2"] == pytest.approx(0.0)  # no outgoing

    def test_different_faction_not_counted(self):
        reps = [
            {"id": "r1", "faction": "F1"},
            {"id": "r2", "faction": "F2"},
        ]
        rels = [{"from": "r1", "to": "r2", "betrayal_prob": 0.9}]
        avg = compute_faction_betrayal_avg(reps, rels)
        assert avg["r1"] == pytest.approx(0.0)

    def test_multiple_same_faction_members(self):
        reps = [
            {"id": "r1", "faction": "F1"},
            {"id": "r2", "faction": "F1"},
            {"id": "r3", "faction": "F1"},
        ]
        rels = [
            {"from": "r1", "to": "r2", "betrayal_prob": 0.6},
            {"from": "r1", "to": "r3", "betrayal_prob": 0.8},
        ]
        avg = compute_faction_betrayal_avg(reps, rels)
        assert avg["r1"] == pytest.approx(0.7)

    def test_no_relations(self):
        reps = [{"id": "r1", "faction": "F1"}]
        avg = compute_faction_betrayal_avg(reps, [])
        assert avg["r1"] == pytest.approx(0.0)


class TestEngineerFeatures:
    def test_integration(self):
        data = {
            "representatives": [
                {"id": "r1", "faction": "F1", "influence": 80},
                {"id": "r2", "faction": "F1", "influence": 60},
            ],
            "proposals": [
                {"id": "p1", "priority": 8},
                {"id": "p2", "priority": 5},
            ],
            "objections": [
                {"rep_id": "r1", "proposal_id": "p1", "severity": 7},
            ],
            "relations": [
                {"from": "r1", "to": "r2", "trust": 80, "betrayal_prob": 0.1},
                {"from": "r2", "to": "r1", "trust": 70, "betrayal_prob": 0.2},
            ],
        }
        features = engineer_features(data)

        assert ("r1", "r2") in features["relationship_scores"]
        assert ("r2", "r1") in features["relationship_scores"]
        assert "p1" in features["objection_weights"]
        assert "p1" in features["proposal_viability"]
        assert "p2" in features["proposal_viability"]
        assert "r1" in features["faction_betrayal_avg"]
        assert "r2" in features["faction_betrayal_avg"]

        # r1→r2: 80*(1-0.1)=72
        assert features["relationship_scores"][("r1", "r2")] == pytest.approx(72.0)
        # objection weight p1: 7 * 80 = 560
        assert features["objection_weights"]["p1"] == pytest.approx(560.0)
        # p2 has no objections → viability = 5 * (1 - 0) = 5
        assert features["proposal_viability"]["p2"] == pytest.approx(5.0)
