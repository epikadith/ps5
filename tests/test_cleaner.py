"""
Tests for Phase 2: Data Cleaning Layer
"""

import pytest
from src.cleaner import (
    clean_representatives, clean_proposals, clean_objections,
    clean_relations, clean_all_data, _safe_numeric,
)


class TestSafeNumeric:
    def test_valid_int(self):
        assert _safe_numeric(85) == 85.0

    def test_string_int(self):
        assert _safe_numeric("85") == 85.0

    def test_none_returns_default(self):
        assert _safe_numeric(None, default=50.0) == 50.0

    def test_none_no_default(self):
        assert _safe_numeric(None) is None

    def test_invalid_string(self):
        assert _safe_numeric("high") is None

    def test_clamp_upper(self):
        assert _safe_numeric(150, max_val=100) == 100.0

    def test_clamp_lower(self):
        assert _safe_numeric(-5, min_val=0) == 0.0


class TestCleanRepresentatives:
    def test_null_influence_imputed(self):
        reps = [
            {"id": "rep_001", "influence": 80},
            {"id": "rep_002", "influence": None},
            {"id": "rep_003", "influence": 100},
        ]
        result = clean_representatives(reps)
        rep_002 = next(r for r in result if r["id"] == "rep_002")
        assert rep_002["influence"] == 90.0

    def test_string_influence_cast(self):
        reps = [{"id": "rep_001", "influence": "85"}]
        result = clean_representatives(reps)
        assert result[0]["influence"] == 85.0

    def test_out_of_range_clamped(self):
        reps = [{"id": "rep_001", "influence": 150}]
        result = clean_representatives(reps)
        assert result[0]["influence"] == 100.0

    def test_negative_influence_clamped(self):
        reps = [{"id": "rep_001", "influence": -10}]
        result = clean_representatives(reps)
        assert result[0]["influence"] == 0.0

    def test_deduplication_keeps_first(self):
        reps = [
            {"id": "rep_001", "name": "First", "influence": 80},
            {"id": "rep_001", "name": "Dup", "influence": 90},
        ]
        result = clean_representatives(reps)
        assert len(result) == 1
        assert result[0]["name"] == "First"

    def test_all_null_influence(self):
        reps = [
            {"id": "rep_001", "influence": None},
            {"id": "rep_002", "influence": None},
        ]
        result = clean_representatives(reps)
        for rep in result:
            assert rep["influence"] == 50.0

    def test_invalid_string_influence(self):
        reps = [
            {"id": "rep_001", "influence": "high"},
            {"id": "rep_002", "influence": 80},
        ]
        result = clean_representatives(reps)
        rep_001 = next(r for r in result if r["id"] == "rep_001")
        assert rep_001["influence"] == 80.0


class TestCleanProposals:
    def test_dedup_keeps_first(self):
        props = [
            {"id": "prop_001", "title": "First", "sponsor": "rep_001", "priority": 8},
            {"id": "prop_001", "title": "Dup", "sponsor": "rep_001", "priority": 5},
        ]
        result = clean_proposals(props, {"rep_001"})
        assert len(result) == 1
        assert result[0]["title"] == "First"

    def test_ghost_sponsor_filtered(self):
        props = [
            {"id": "prop_001", "sponsor": "rep_001", "priority": 8},
            {"id": "prop_002", "sponsor": "rep_099", "priority": 6},
        ]
        result = clean_proposals(props, {"rep_001"})
        assert len(result) == 1

    def test_priority_clamp(self):
        props = [
            {"id": "p1", "sponsor": "r1", "priority": "8"},
            {"id": "p2", "sponsor": "r1", "priority": 15},
            {"id": "p3", "sponsor": "r1", "priority": -1},
        ]
        result = clean_proposals(props, {"r1"})
        assert result[0]["priority"] == 8.0
        assert result[1]["priority"] == 10.0
        assert result[2]["priority"] == 1.0

    def test_null_priority_defaults(self):
        props = [{"id": "p1", "sponsor": "r1", "priority": None}]
        result = clean_proposals(props, {"r1"})
        assert result[0]["priority"] == 5.0


class TestCleanObjections:
    def test_ghost_rep_filtered(self):
        objs = [
            {"rep_id": "rep_001", "proposal_id": "prop_001", "severity": 5},
            {"rep_id": "rep_099", "proposal_id": "prop_001", "severity": 7},
        ]
        result = clean_objections(objs, {"rep_001"}, {"prop_001"})
        assert len(result) == 1

    def test_ghost_proposal_filtered(self):
        objs = [{"rep_id": "rep_001", "proposal_id": "prop_999", "severity": 5}]
        result = clean_objections(objs, {"rep_001"}, {"prop_001"})
        assert len(result) == 0

    def test_severity_clamp(self):
        objs = [
            {"rep_id": "r1", "proposal_id": "p1", "severity": -3},
            {"rep_id": "r2", "proposal_id": "p1", "severity": 15},
        ]
        result = clean_objections(objs, {"r1", "r2"}, {"p1"})
        assert result[0]["severity"] == 1.0
        assert result[1]["severity"] == 10.0

    def test_string_severity(self):
        objs = [{"rep_id": "r1", "proposal_id": "p1", "severity": "high"}]
        result = clean_objections(objs, {"r1"}, {"p1"})
        assert result[0]["severity"] == 5.0

    def test_null_severity(self):
        objs = [{"rep_id": "r1", "proposal_id": "p1", "severity": None}]
        result = clean_objections(objs, {"r1"}, {"p1"})
        assert result[0]["severity"] == 5.0

    def test_dedup_pair(self):
        objs = [
            {"rep_id": "r1", "proposal_id": "p1", "severity": 8},
            {"rep_id": "r1", "proposal_id": "p1", "severity": 6},
        ]
        result = clean_objections(objs, {"r1"}, {"p1"})
        assert len(result) == 1
        assert result[0]["severity"] == 8.0


class TestCleanRelations:
    def test_ghost_from_filtered(self):
        rels = [{"from": "r99", "to": "r1", "trust": "80", "rivalry": "20", "betrayal_prob": "0.1"}]
        result = clean_relations(rels, {"r1"})
        assert len(result) == 0

    def test_trust_clamped(self):
        rels = [{"from": "r1", "to": "r2", "trust": "150", "rivalry": "20", "betrayal_prob": "0.1"}]
        result = clean_relations(rels, {"r1", "r2"})
        assert result[0]["trust"] == 100.0

    def test_null_trust(self):
        rels = [{"from": "r1", "to": "r2", "trust": "", "rivalry": "20", "betrayal_prob": "0.1"}]
        result = clean_relations(rels, {"r1", "r2"})
        assert result[0]["trust"] == 0.0

    def test_dirty_rivalry(self):
        rels = [{"from": "r1", "to": "r2", "trust": "80", "rivalry": "high", "betrayal_prob": "0.1"}]
        result = clean_relations(rels, {"r1", "r2"})
        assert result[0]["rivalry"] == 50.0

    def test_betrayal_clamped(self):
        rels = [{"from": "r1", "to": "r2", "trust": "80", "rivalry": "20", "betrayal_prob": "1.5"}]
        result = clean_relations(rels, {"r1", "r2"})
        assert result[0]["betrayal_prob"] == 1.0

    def test_dedup_pair(self):
        rels = [
            {"from": "r1", "to": "r2", "trust": "80", "rivalry": "20", "betrayal_prob": "0.1"},
            {"from": "r1", "to": "r2", "trust": "90", "rivalry": "10", "betrayal_prob": "0.05"},
        ]
        result = clean_relations(rels, {"r1", "r2"})
        assert len(result) == 1
        assert result[0]["trust"] == 80.0

    def test_self_relations_filtered(self):
        rels = [{"from": "r1", "to": "r1", "trust": "100", "rivalry": "0", "betrayal_prob": "0.0"}]
        result = clean_relations(rels, {"r1"})
        assert len(result) == 0


class TestCleanAllData:
    def test_full_pipeline(self):
        data = {
            "representatives": [
                {"id": "rep_001", "name": "A", "faction": "F1", "influence": 85},
                {"id": "rep_002", "name": "B", "faction": "F2", "influence": "70"},
                {"id": "rep_003", "name": "C", "faction": "F1", "influence": None},
                {"id": "rep_001", "name": "Dup", "faction": "F1", "influence": 80},
                {"id": "rep_004", "name": "D", "faction": "F2", "influence": 150},
            ],
            "proposals": [
                {"id": "prop_001", "sponsor": "rep_001", "priority": 8},
                {"id": "prop_002", "sponsor": "rep_099", "priority": 10},
                {"id": "prop_001", "sponsor": "rep_002", "priority": 5},
            ],
            "objections": [
                {"rep_id": "rep_001", "proposal_id": "prop_001", "severity": 5},
                {"rep_id": "rep_099", "proposal_id": "prop_001", "severity": 7},
            ],
            "relations": [
                {"from": "rep_001", "to": "rep_002", "trust": "80", "rivalry": "20", "betrayal_prob": "0.1"},
                {"from": "rep_099", "to": "rep_001", "trust": "50", "rivalry": "30", "betrayal_prob": "0.2"},
            ],
        }
        result = clean_all_data(data)

        assert len(result["representatives"]) == 4
        rep_ids = {r["id"] for r in result["representatives"]}
        assert rep_ids == {"rep_001", "rep_002", "rep_003", "rep_004"}

        rep_004 = next(r for r in result["representatives"] if r["id"] == "rep_004")
        assert rep_004["influence"] == 100.0

        rep_003 = next(r for r in result["representatives"] if r["id"] == "rep_003")
        assert rep_003["influence"] is not None

        assert len(result["proposals"]) == 1
        assert result["proposals"][0]["id"] == "prop_001"

        assert len(result["objections"]) == 1
        assert result["objections"][0]["rep_id"] == "rep_001"

        assert len(result["relations"]) == 1
        assert result["relations"][0]["from"] == "rep_001"
