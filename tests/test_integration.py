"""
Integration tests: Full pipeline (Phases 1-6).
Phase 6: Public format validation tests.
"""

import json
import os
import pytest

from consensus_engine import run_pipeline
from src.data_loader import load_all_data
from src.cleaner import clean_all_data


class TestFullPipeline:
    """Integration tests for the complete pipeline."""

    @pytest.fixture
    def real_data_dir(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "raw")
        if not os.path.exists(data_dir):
            pytest.skip("data/raw/ directory not found")
        return data_dir

    @pytest.fixture
    def output_file(self, tmp_path):
        return str(tmp_path / "output" / "final_agreement.json")

    def test_pipeline_produces_valid_json(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        assert os.path.exists(output_file)
        with open(output_file) as f:
            parsed = json.load(f)
        assert parsed == output

    def test_output_schema(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        assert "final_agreement" in output
        assert "proposals" in output["final_agreement"]
        assert "supporting_reps" in output["final_agreement"]
        assert "alliances" in output

    def test_at_least_one_proposal(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        assert len(output["final_agreement"]["proposals"]) >= 1

    def test_at_least_one_supporter(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        assert len(output["final_agreement"]["supporting_reps"]) >= 1

    def test_proposals_are_strings(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        for p in output["final_agreement"]["proposals"]:
            assert isinstance(p, str)

    def test_supporters_are_strings(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        for s in output["final_agreement"]["supporting_reps"]:
            assert isinstance(s, str)

    def test_alliances_is_list(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        assert isinstance(output["alliances"], list)

    def test_alliances_are_pairs_of_strings(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        for alliance in output["alliances"]:
            assert isinstance(alliance, list)
            assert len(alliance) == 2
            for member in alliance:
                assert isinstance(member, str)

    def test_no_duplicate_proposals(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        proposals = output["final_agreement"]["proposals"]
        assert len(proposals) == len(set(proposals))

    def test_no_duplicate_supporters(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        supporters = output["final_agreement"]["supporting_reps"]
        assert len(supporters) == len(set(supporters))

    def test_all_ids_normalized(self, real_data_dir, output_file):
        output = run_pipeline(real_data_dir, output_file)
        for p in output["final_agreement"]["proposals"]:
            assert p == p.strip().lower(), f"Proposal ID not normalized: '{p}'"
        for s in output["final_agreement"]["supporting_reps"]:
            assert s == s.strip().lower(), f"Supporter ID not normalized: '{s}'"
        for alliance in output["alliances"]:
            for member in alliance:
                assert member == member.strip().lower(), f"Alliance member not normalized: '{member}'"


class TestPublicFormatValidation:
    """
    Phase 6: Public format validation tests.
    These mirror the 13 public tests that check format correctness.
    """

    @pytest.fixture
    def real_data_dir(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "raw")
        if not os.path.exists(data_dir):
            pytest.skip("data/raw/ directory not found")
        return data_dir

    @pytest.fixture
    def output(self, real_data_dir, tmp_path):
        output_file = str(tmp_path / "output" / "final_agreement.json")
        return run_pipeline(real_data_dir, output_file)

    @pytest.fixture
    def clean_data(self, real_data_dir):
        raw = load_all_data(real_data_dir)
        return clean_all_data(raw)

    # --- Test 1: Valid JSON ---
    def test_output_is_valid_json(self, output):
        """Output must be valid JSON (serializable)."""
        json_str = json.dumps(output)
        parsed = json.loads(json_str)
        assert parsed is not None

    # --- Test 2: Top-level keys ---
    def test_has_final_agreement_key(self, output):
        assert "final_agreement" in output

    def test_has_alliances_key(self, output):
        assert "alliances" in output

    # --- Test 3: final_agreement structure ---
    def test_final_agreement_has_proposals(self, output):
        assert "proposals" in output["final_agreement"]

    def test_final_agreement_has_supporting_reps(self, output):
        assert "supporting_reps" in output["final_agreement"]

    # --- Test 4: Types ---
    def test_proposals_is_list(self, output):
        assert isinstance(output["final_agreement"]["proposals"], list)

    def test_supporting_reps_is_list(self, output):
        assert isinstance(output["final_agreement"]["supporting_reps"], list)

    def test_alliances_is_list_of_lists(self, output):
        assert isinstance(output["alliances"], list)
        for a in output["alliances"]:
            assert isinstance(a, list)

    # --- Test 5: Non-empty ---
    def test_at_least_one_proposal(self, output):
        assert len(output["final_agreement"]["proposals"]) >= 1

    def test_at_least_one_supporter(self, output):
        assert len(output["final_agreement"]["supporting_reps"]) >= 1

    # --- Test 6: All proposal IDs exist in input ---
    def test_all_proposal_ids_exist_in_input(self, output, clean_data):
        valid_ids = {p["id"] for p in clean_data["proposals"]}
        for pid in output["final_agreement"]["proposals"]:
            assert pid in valid_ids, f"Proposal '{pid}' not found in input"

    # --- Test 7: All supporter IDs exist in input ---
    def test_all_supporter_ids_exist_in_input(self, output, clean_data):
        valid_ids = {r["id"] for r in clean_data["representatives"]}
        for sid in output["final_agreement"]["supporting_reps"]:
            assert sid in valid_ids, f"Supporter '{sid}' not found in input"

    # --- Test 8: All alliance member IDs exist in input ---
    def test_all_alliance_member_ids_exist_in_input(self, output, clean_data):
        valid_ids = {r["id"] for r in clean_data["representatives"]}
        for alliance in output["alliances"]:
            for member in alliance:
                assert member in valid_ids, f"Alliance member '{member}' not found in input"

    # --- Test 9: No duplicate proposals ---
    def test_no_duplicate_proposals(self, output):
        proposals = output["final_agreement"]["proposals"]
        assert len(proposals) == len(set(proposals))

    # --- Test 10: No duplicate supporters ---
    def test_no_duplicate_supporters(self, output):
        supporters = output["final_agreement"]["supporting_reps"]
        assert len(supporters) == len(set(supporters))

    # --- Test 11: Alliance pairs are valid (2 elements each) ---
    def test_alliance_pairs_have_two_members(self, output):
        for alliance in output["alliances"]:
            assert len(alliance) == 2

    # --- Test 12: No duplicate alliance pairs ---
    def test_no_duplicate_alliance_pairs(self, output):
        seen = set()
        for alliance in output["alliances"]:
            pair = tuple(sorted(alliance))
            assert pair not in seen, f"Duplicate alliance: {alliance}"
            seen.add(pair)

    # --- Test 13: Alliance members are different ---
    def test_alliance_members_are_different(self, output):
        for alliance in output["alliances"]:
            assert alliance[0] != alliance[1], f"Self-alliance: {alliance}"


class TestMinimalPipeline:
    """Test with minimal synthetic data."""

    @pytest.fixture
    def minimal_data_dir(self, tmp_path):
        reps = [{"id": "rep_001", "name": "A", "faction": "F1", "influence": 80}]
        props = [{"id": "prop_001", "title": "Test", "sponsor": "rep_001", "priority": 8}]
        objs = []
        with open(tmp_path / "representatives.json", "w") as f:
            json.dump(reps, f)
        with open(tmp_path / "proposals.json", "w") as f:
            json.dump(props, f)
        with open(tmp_path / "objections.json", "w") as f:
            json.dump(objs, f)
        with open(tmp_path / "relations.csv", "w") as f:
            f.write("from,to,trust,rivalry,betrayal_prob,last_interaction\n")
        return str(tmp_path)

    def test_minimal_viable(self, minimal_data_dir, tmp_path):
        output_file = str(tmp_path / "out" / "result.json")
        output = run_pipeline(minimal_data_dir, output_file)
        assert len(output["final_agreement"]["proposals"]) >= 1
        assert len(output["final_agreement"]["supporting_reps"]) >= 1
        assert isinstance(output["alliances"], list)


class TestStrategicCorrectness:
    """Tests for strategic correctness with the real data."""

    @pytest.fixture
    def real_data_dir(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "raw")
        if not os.path.exists(data_dir):
            pytest.skip("data/raw/ directory not found")
        return data_dir

    @pytest.fixture
    def output(self, real_data_dir, tmp_path):
        output_file = str(tmp_path / "output" / "final_agreement.json")
        return run_pipeline(real_data_dir, output_file)

    def test_ghost_sponsor_proposal_excluded(self, output):
        """prop_005 has ghost sponsor rep_099 → should NOT be in output."""
        assert "prop_005" not in output["final_agreement"]["proposals"]

    def test_supporters_dont_include_trojan_horses(self, real_data_dir, output, tmp_path):
        """Supporters should not include high-betrayal reps."""
        from src.data_loader import load_all_data
        from src.cleaner import clean_all_data
        from src.consensus_builder import filter_trojan_horses

        raw = load_all_data(real_data_dir)
        data = clean_all_data(raw)
        trojans = filter_trojan_horses(data["representatives"], data["relations"])
        for t in trojans:
            assert t not in output["final_agreement"]["supporting_reps"]
