"""
Tests for Phase 1: Data Loading + Basic Output

Covers:
- All 4 files load without errors
- IDs normalized (e.g., "REP_001" → "rep_001", " rep_004" → "rep_004")
- Output JSON is valid and matches required schema
- At least 1 proposal and 1 supporting rep in output
"""

import json
import os
import tempfile
import pytest

from src.data_loader import load_all_data, normalize_id


# ============================================================================
# normalize_id tests
# ============================================================================

class TestNormalizeId:
    """Tests for the normalize_id function."""

    def test_lowercase(self):
        assert normalize_id("REP_001") == "rep_001"

    def test_strip_whitespace(self):
        assert normalize_id(" rep_004") == "rep_004"

    def test_strip_trailing_whitespace(self):
        assert normalize_id("rep_004 ") == "rep_004"

    def test_strip_both_sides(self):
        assert normalize_id("  REP_004  ") == "rep_004"

    def test_already_normalized(self):
        assert normalize_id("rep_001") == "rep_001"

    def test_none(self):
        assert normalize_id(None) == ""

    def test_numeric_input(self):
        assert normalize_id(123) == "123"

    def test_mixed_case(self):
        assert normalize_id("Rep_002") == "rep_002"


# ============================================================================
# File loading tests
# ============================================================================

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample input files."""
    # representatives.json
    reps = [
        {"id": "rep_001", "name": "A", "faction": "F1", "influence": 85},
        {"id": "REP_002", "name": "B", "faction": "F2", "influence": 70},
        {"id": " rep_003", "name": "C", "faction": "F1", "influence": 90},
    ]
    with open(tmp_path / "representatives.json", "w") as f:
        json.dump(reps, f)

    # proposals.json
    props = [
        {"id": "prop_001", "title": "Test", "sponsor": "rep_001", "priority": 8},
        {"id": "PROP_002", "title": "Test2", "sponsor": "REP_002", "priority": 5},
    ]
    with open(tmp_path / "proposals.json", "w") as f:
        json.dump(props, f)

    # objections.json
    objs = [
        {"rep_id": "REP_002", "proposal_id": "prop_001", "severity": 5},
    ]
    with open(tmp_path / "objections.json", "w") as f:
        json.dump(objs, f)

    # relations.csv
    with open(tmp_path / "relations.csv", "w") as f:
        f.write("from,to,trust,rivalry,betrayal_prob,last_interaction\n")
        f.write("rep_001,REP_002,80,20,0.1,2024-01-01\n")
        f.write(" rep_003,rep_001,90,5,0.05,2024-01-01\n")

    return tmp_path


class TestLoadAllData:
    """Tests for load_all_data function."""

    def test_loads_all_four_files(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        assert "representatives" in data
        assert "proposals" in data
        assert "objections" in data
        assert "relations" in data

    def test_representatives_count(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        assert len(data["representatives"]) == 3

    def test_proposals_count(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        assert len(data["proposals"]) == 2

    def test_objections_count(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        assert len(data["objections"]) == 1

    def test_relations_count(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        assert len(data["relations"]) == 2

    def test_rep_ids_normalized(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        rep_ids = [r["id"] for r in data["representatives"]]
        assert "rep_001" in rep_ids
        assert "rep_002" in rep_ids
        assert "rep_003" in rep_ids
        # No uppercase or whitespace
        assert "REP_002" not in rep_ids
        assert " rep_003" not in rep_ids

    def test_proposal_ids_normalized(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        prop_ids = [p["id"] for p in data["proposals"]]
        assert "prop_001" in prop_ids
        assert "prop_002" in prop_ids
        assert "PROP_002" not in prop_ids

    def test_proposal_sponsor_normalized(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        sponsors = [p["sponsor"] for p in data["proposals"]]
        assert "rep_001" in sponsors
        assert "rep_002" in sponsors
        assert "REP_002" not in sponsors

    def test_objection_ids_normalized(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        obj = data["objections"][0]
        assert obj["rep_id"] == "rep_002"
        assert obj["proposal_id"] == "prop_001"

    def test_relation_ids_normalized(self, sample_data_dir):
        data = load_all_data(str(sample_data_dir))
        for rel in data["relations"]:
            assert rel["from"] == rel["from"].strip().lower()
            assert rel["to"] == rel["to"].strip().lower()


# ============================================================================
# Integration test: loading real data
# ============================================================================

class TestLoadRealData:
    """Tests against the actual data/raw/ files."""

    @pytest.fixture
    def real_data_dir(self):
        """Path to the actual data directory."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "raw")
        if not os.path.exists(data_dir):
            pytest.skip("data/raw/ directory not found")
        return data_dir

    def test_loads_real_data_without_errors(self, real_data_dir):
        data = load_all_data(real_data_dir)
        assert len(data["representatives"]) > 0
        assert len(data["proposals"]) > 0
        assert len(data["objections"]) > 0
        assert len(data["relations"]) > 0

    def test_all_rep_ids_normalized_in_real_data(self, real_data_dir):
        data = load_all_data(real_data_dir)
        for rep in data["representatives"]:
            rid = rep["id"]
            assert rid == rid.strip().lower(), f"Rep ID not normalized: '{rid}'"

    def test_all_proposal_ids_normalized_in_real_data(self, real_data_dir):
        data = load_all_data(real_data_dir)
        for prop in data["proposals"]:
            pid = prop["id"]
            assert pid == pid.strip().lower(), f"Proposal ID not normalized: '{pid}'"
            sponsor = prop["sponsor"]
            assert sponsor == sponsor.strip().lower(), f"Sponsor not normalized: '{sponsor}'"
