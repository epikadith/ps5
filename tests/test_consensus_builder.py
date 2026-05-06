"""
Tests for Phase 4: Strategic Logic - Trojan & Poison Filters
"""

import pytest
from src.consensus_builder import (
    filter_trojan_horses, filter_poison_pills,
    select_proposals, select_supporters, build_consensus,
)


class TestFilterTrojanHorses:
    """Tests for Trojan Horse detection."""

    def test_high_betrayal_excluded(self):
        """Rep with avg betrayal > 0.3 should be flagged."""
        reps = [{"id": "r1"}, {"id": "r2"}]
        rels = [
            {"from": "r1", "to": "r2", "betrayal_prob": 0.9},
        ]
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "r1" in trojans

    def test_low_betrayal_not_excluded(self):
        """Rep with avg betrayal <= 0.3 should NOT be flagged."""
        reps = [{"id": "r1"}, {"id": "r2"}]
        rels = [
            {"from": "r1", "to": "r2", "betrayal_prob": 0.1},
        ]
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "r1" not in trojans

    def test_average_across_multiple_relations(self):
        """Avg betrayal across multiple outgoing relations."""
        reps = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        rels = [
            {"from": "r1", "to": "r2", "betrayal_prob": 0.1},
            {"from": "r1", "to": "r3", "betrayal_prob": 0.2},
        ]
        # avg = 0.15, below 0.3
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "r1" not in trojans

    def test_high_avg_across_multiple(self):
        """Avg betrayal above threshold across multiple relations."""
        reps = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        rels = [
            {"from": "r1", "to": "r2", "betrayal_prob": 0.4},
            {"from": "r1", "to": "r3", "betrayal_prob": 0.6},
        ]
        # avg = 0.5, above 0.3
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "r1" in trojans

    def test_no_relations(self):
        """Rep with no outgoing relations is not a Trojan."""
        reps = [{"id": "r1"}]
        trojans = filter_trojan_horses(reps, [], betrayal_threshold=0.3)
        assert len(trojans) == 0

    def test_threshold_boundary(self):
        """Exactly at threshold should NOT be flagged (> not >=)."""
        reps = [{"id": "r1"}, {"id": "r2"}]
        rels = [{"from": "r1", "to": "r2", "betrayal_prob": 0.3}]
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "r1" not in trojans

    def test_classic_trojan_horse_scenario(self):
        """High influence rep with high betrayal: influence=98, betrayal=0.95."""
        reps = [
            {"id": "trojan", "influence": 98},
            {"id": "normal", "influence": 50},
        ]
        rels = [
            {"from": "trojan", "to": "normal", "betrayal_prob": 0.95},
        ]
        trojans = filter_trojan_horses(reps, rels, betrayal_threshold=0.3)
        assert "trojan" in trojans
        assert "normal" not in trojans


class TestFilterPoisonPills:
    """Tests for Poison Pill proposal filtering."""

    def test_high_objection_rejected(self):
        """Proposal with objection_weight > cap should be filtered."""
        props = [
            {"id": "p1", "priority": 10},
            {"id": "p2", "priority": 5},
        ]
        weights = {"p1": 100.0, "p2": 30.0}
        viable = filter_poison_pills(props, weights, objection_cap=50)
        ids = [p["id"] for p in viable]
        assert "p1" not in ids
        assert "p2" in ids

    def test_no_objections_all_pass(self):
        """Proposals with no objections should all pass."""
        props = [{"id": "p1"}, {"id": "p2"}]
        viable = filter_poison_pills(props, {}, objection_cap=50)
        assert len(viable) == 2

    def test_at_cap_passes(self):
        """Proposal with objection_weight == cap should pass (<= not <)."""
        props = [{"id": "p1"}]
        weights = {"p1": 50.0}
        viable = filter_poison_pills(props, weights, objection_cap=50)
        assert len(viable) == 1

    def test_all_poison_pills(self):
        """If all proposals are Poison Pills, empty list returned."""
        props = [{"id": "p1"}, {"id": "p2"}]
        weights = {"p1": 100.0, "p2": 200.0}
        viable = filter_poison_pills(props, weights, objection_cap=50)
        assert len(viable) == 0


class TestSelectProposals:
    """Tests for proposal selection by viability."""

    def test_sorted_by_viability(self):
        """Proposals should be sorted by viability (highest first)."""
        props = [
            {"id": "p1", "priority": 5},
            {"id": "p2", "priority": 8},
            {"id": "p3", "priority": 3},
        ]
        viability = {"p1": 4.0, "p2": 8.0, "p3": 2.0}
        result = select_proposals(props, viability)
        assert result == ["p2", "p1", "p3"]

    def test_empty_proposals(self):
        result = select_proposals([], {})
        assert result == []


class TestSelectSupporters:
    """Tests for supporter selection."""

    def test_excludes_trojans(self):
        """Trojan Horse reps should be excluded from supporters."""
        reps = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        objs = []
        trojans = {"r2"}
        result = select_supporters(reps, objs, ["p1"], trojans)
        assert "r2" not in result
        assert "r1" in result
        assert "r3" in result

    def test_excludes_objectors(self):
        """Reps who object to selected proposals should be excluded."""
        reps = [{"id": "r1"}, {"id": "r2"}]
        objs = [{"rep_id": "r1", "proposal_id": "p1", "severity": 5}]
        result = select_supporters(reps, objs, ["p1"], set())
        assert "r1" not in result
        assert "r2" in result

    def test_objections_to_unselected_ok(self):
        """Objections to non-selected proposals shouldn't exclude the rep."""
        reps = [{"id": "r1"}]
        objs = [{"rep_id": "r1", "proposal_id": "p2", "severity": 5}]
        result = select_supporters(reps, objs, ["p1"], set())
        assert "r1" in result

    def test_both_trojan_and_objector(self):
        """Rep that is both Trojan and objector should be excluded."""
        reps = [{"id": "r1"}, {"id": "r2"}]
        objs = [{"rep_id": "r1", "proposal_id": "p1", "severity": 5}]
        trojans = {"r1"}
        result = select_supporters(reps, objs, ["p1"], trojans)
        assert "r1" not in result


class TestBuildConsensus:
    """Integration tests for the full consensus builder."""

    def test_basic_consensus(self):
        """Basic scenario: one Trojan, one Poison Pill."""
        data = {
            "representatives": [
                {"id": "r1", "influence": 80},
                {"id": "r2", "influence": 90},
                {"id": "r3", "influence": 50},
            ],
            "proposals": [
                {"id": "p1", "priority": 8},
                {"id": "p2", "priority": 10},
            ],
            "objections": [
                {"rep_id": "r3", "proposal_id": "p2", "severity": 8},
            ],
            "relations": [
                {"from": "r2", "to": "r1", "betrayal_prob": 0.9},
                {"from": "r2", "to": "r3", "betrayal_prob": 0.8},
                {"from": "r1", "to": "r3", "betrayal_prob": 0.1},
            ],
        }
        features = {
            "objection_weights": {"p2": 400.0},  # 8 * 50 = 400 > 50
            "proposal_viability": {"p1": 8.0, "p2": 0.0},
        }
        result = build_consensus(data, features, betrayal_threshold=0.3, objection_cap=50)

        assert "r2" in result["trojan_horses"]
        assert "p2" not in result["selected_proposals"]
        assert "p1" in result["selected_proposals"]
        assert "r2" not in result["supporters"]

    def test_at_least_one_proposal_fallback(self):
        """When all proposals are Poison Pills, fallback picks the least-objected."""
        data = {
            "representatives": [{"id": "r1", "influence": 80}],
            "proposals": [
                {"id": "p1", "priority": 10},
                {"id": "p2", "priority": 8},
            ],
            "objections": [],
            "relations": [],
        }
        features = {
            "objection_weights": {"p1": 100.0, "p2": 80.0},
            "proposal_viability": {"p1": 0.0, "p2": 2.0},
        }
        result = build_consensus(data, features, objection_cap=50)
        assert len(result["selected_proposals"]) >= 1

    def test_at_least_one_supporter_fallback(self):
        """When all eligible reps object, fallback picks the best candidate."""
        data = {
            "representatives": [
                {"id": "r1", "influence": 80},
                {"id": "r2", "influence": 60},
            ],
            "proposals": [{"id": "p1", "priority": 8}],
            "objections": [
                {"rep_id": "r1", "proposal_id": "p1", "severity": 5},
                {"rep_id": "r2", "proposal_id": "p1", "severity": 3},
            ],
            "relations": [],
        }
        features = {
            "objection_weights": {"p1": 30.0},
            "proposal_viability": {"p1": 8.0},
        }
        result = build_consensus(data, features, objection_cap=50)
        assert len(result["supporters"]) >= 1
