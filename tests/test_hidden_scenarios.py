"""
Phase 7: Hidden Tests Coverage

18 scenario-based tests that simulate the hidden strategic tests:
1. Trojan Horse
2. Poison Pill
3. False Friend
4. Clear Alliance
5. Faction War
6. Priority vs Objection
7. Supporter Coherence
8. Faction Infiltrator
9. Cascading Betrayal
10. Alliance Hijack
11. Complete Rivalry
12. Ghost Sponsor
13. Minimum Viable
14. ID Normalization
15. Duplicate Proposals
16. Null Influence
17. Scale Correctness
18. Dirty CSV
"""

import json
import os
import time
import pytest

from consensus_engine import run_pipeline


def _make_data_dir(tmp_path, reps, props, objs, rels_header, rels_rows):
    """Helper to create a temp data directory from in-memory data."""
    d = tmp_path / "data"
    d.mkdir(exist_ok=True)
    with open(d / "representatives.json", "w") as f:
        json.dump(reps, f)
    with open(d / "proposals.json", "w") as f:
        json.dump(props, f)
    with open(d / "objections.json", "w") as f:
        json.dump(objs, f)
    with open(d / "relations.csv", "w") as f:
        f.write(rels_header + "\n")
        for row in rels_rows:
            f.write(row + "\n")
    return str(d)


class TestHidden01TrojanHorse:
    """Did you exclude the high-betrayal rep?"""

    def test_trojan_excluded_from_supporters(self, tmp_path):
        reps = [
            {"id": "rep_001", "name": "Honest", "faction": "A", "influence": 50},
            {"id": "rep_002", "name": "Trojan", "faction": "B", "influence": 98},
        ]
        props = [{"id": "prop_001", "title": "Bill", "sponsor": "rep_001", "priority": 8}]
        objs = []
        rels = ["rep_002,rep_001,90,5,0.95,2024-01-01"]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert "rep_002" not in output["final_agreement"]["supporting_reps"]
        assert "rep_001" in output["final_agreement"]["supporting_reps"]


class TestHidden02PoisonPill:
    """Did you avoid the universally-objected proposal?"""

    def test_poison_pill_avoided(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F", "influence": 90},
            {"id": "r2", "name": "B", "faction": "F", "influence": 80},
        ]
        props = [
            {"id": "p_poison", "title": "Poison", "sponsor": "r1", "priority": 10},
            {"id": "p_safe", "title": "Safe", "sponsor": "r2", "priority": 5},
        ]
        objs = [
            {"rep_id": "r1", "proposal_id": "p_poison", "severity": 10},
            {"rep_id": "r2", "proposal_id": "p_poison", "severity": 10},
        ]
        rels = ["r1,r2,70,20,0.1,2024-01-01", "r2,r1,65,25,0.15,2024-01-01"]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # p_poison has weight = (10*90 + 10*80) = 1700 > 50
        # p_safe has weight = 0 <= 50
        assert "p_safe" in output["final_agreement"]["proposals"]


class TestHidden03FalseFriend:
    """Did you detect asymmetric trust?"""

    def test_false_friend_not_allied(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F2", "influence": 70},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = []
        # A trusts B a lot (95) but B barely trusts A (25)
        rels = [
            "r1,r2,95,5,0.05,2024-01-01",
            "r2,r1,25,70,0.85,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert ["r1", "r2"] not in output["alliances"]


class TestHidden04ClearAlliance:
    """Did you detect a genuine strong alliance?"""

    def test_clear_alliance_detected(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F2", "influence": 75},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = []
        rels = [
            "r1,r2,85,10,0.05,2024-01-01",
            "r2,r1,90,5,0.02,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert ["r1", "r2"] in output["alliances"]


class TestHidden05FactionWar:
    """Did you pick the least-objected proposal?"""

    def test_least_objected_proposal_selected(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F2", "influence": 70},
            {"id": "r3", "name": "C", "faction": "F3", "influence": 60},
        ]
        props = [
            {"id": "p_heavy", "title": "Heavy", "sponsor": "r1", "priority": 8},
            {"id": "p_light", "title": "Light", "sponsor": "r2", "priority": 7},
        ]
        objs = [
            {"rep_id": "r2", "proposal_id": "p_heavy", "severity": 9},
            {"rep_id": "r3", "proposal_id": "p_heavy", "severity": 8},
        ]
        rels = []
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        proposals = output["final_agreement"]["proposals"]
        # p_light should be viable (no objections, weight=0)
        assert "p_light" in proposals


class TestHidden06PriorityVsObjection:
    """Did objection weight beat raw priority?"""

    def test_objection_beats_priority(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F", "influence": 90},
            {"id": "r2", "name": "B", "faction": "F", "influence": 85},
        ]
        props = [
            {"id": "p_high_pri", "title": "High Pri", "sponsor": "r1", "priority": 10},
            {"id": "p_low_pri", "title": "Low Pri", "sponsor": "r2", "priority": 3},
        ]
        objs = [
            {"rep_id": "r1", "proposal_id": "p_high_pri", "severity": 10},
            {"rep_id": "r2", "proposal_id": "p_high_pri", "severity": 10},
        ]
        rels = ["r1,r2,70,20,0.1,2024-01-01", "r2,r1,65,25,0.1,2024-01-01"]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # p_low_pri has no objections → should pass poison pill filter
        assert "p_low_pri" in output["final_agreement"]["proposals"]


class TestHidden07SupporterCoherence:
    """Did you avoid making objectors into supporters?"""

    def test_objectors_not_supporters(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F", "influence": 70},
            {"id": "r3", "name": "C", "faction": "F", "influence": 60},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = [{"rep_id": "r2", "proposal_id": "p1", "severity": 7}]
        rels = []
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        supporters = output["final_agreement"]["supporting_reps"]
        proposals = output["final_agreement"]["proposals"]
        if "p1" in proposals:
            assert "r2" not in supporters


class TestHidden08FactionInfiltrator:
    """Did you detect a spy in the faction?"""

    def test_infiltrator_excluded_from_alliances(self, tmp_path):
        reps = [
            {"id": "spy", "name": "Spy", "faction": "Progressives", "influence": 85},
            {"id": "loyal1", "name": "Loyal1", "faction": "Progressives", "influence": 70},
            {"id": "loyal2", "name": "Loyal2", "faction": "Progressives", "influence": 65},
            {"id": "outsider", "name": "Outsider", "faction": "Moderates", "influence": 60},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "loyal1", "priority": 7}]
        objs = []
        rels = [
            "spy,loyal1,90,5,0.90,2024-01-01",
            "spy,loyal2,85,10,0.85,2024-01-01",
            "loyal1,spy,80,15,0.10,2024-01-01",
            "loyal2,spy,75,20,0.15,2024-01-01",
            "loyal1,loyal2,80,10,0.05,2024-01-01",
            "loyal2,loyal1,75,15,0.10,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # spy should NOT be in any alliance
        for alliance in output["alliances"]:
            assert "spy" not in alliance


class TestHidden09CascadingBetrayal:
    """Did you exclude the high-risk end of a trust chain?"""

    def test_cascading_betrayal_chain(self, tmp_path):
        # A trusts B, B trusts C, but C has high betrayal
        reps = [
            {"id": "a", "name": "A", "faction": "F", "influence": 80},
            {"id": "b", "name": "B", "faction": "F", "influence": 75},
            {"id": "c", "name": "C", "faction": "F", "influence": 90},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "a", "priority": 8}]
        objs = []
        rels = [
            "a,b,85,10,0.05,2024-01-01",
            "b,a,80,15,0.10,2024-01-01",
            "b,c,90,5,0.05,2024-01-01",
            "c,b,85,10,0.80,2024-01-01",
            "c,a,70,20,0.75,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # C has avg betrayal = (0.80 + 0.75)/2 = 0.775 > 0.3 → Trojan Horse
        assert "c" not in output["final_agreement"]["supporting_reps"]


class TestHidden10AllianceHijack:
    """Did you protect a stable alliance from a disruptor?"""

    def test_alliance_hijack_protection(self, tmp_path):
        reps = [
            {"id": "r1", "name": "Stable1", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "Stable2", "faction": "F1", "influence": 75},
            {"id": "disruptor", "name": "Disruptor", "faction": "F2", "influence": 95},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = []
        # Disruptor has high betrayal toward stable pair, but r1/r2 are low-betrayal
        # r1 avg betrayal: (0.05 + 0.20)/2 = 0.125 → safe
        # r2 avg betrayal: (0.10 + 0.15)/2 = 0.125 → safe
        # disruptor avg betrayal: (0.70 + 0.65)/2 = 0.675 → Trojan
        rels = [
            "r1,r2,85,10,0.05,2024-01-01",
            "r2,r1,80,15,0.10,2024-01-01",
            "disruptor,r1,90,5,0.70,2024-01-01",
            "disruptor,r2,88,8,0.65,2024-01-01",
            "r1,disruptor,40,50,0.20,2024-01-01",
            "r2,disruptor,35,55,0.15,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # r1↔r2 should be allied
        assert ["r1", "r2"] in output["alliances"]
        # Disruptor should NOT be in any alliance
        for alliance in output["alliances"]:
            assert "disruptor" not in alliance


class TestHidden11CompleteRivalry:
    """Did you return empty alliances when everyone is a rival?"""

    def test_complete_rivalry_empty_alliances(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F2", "influence": 70},
            {"id": "r3", "name": "C", "faction": "F3", "influence": 60},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = []
        rels = [
            "r1,r2,10,90,0.90,2024-01-01",
            "r2,r1,15,85,0.85,2024-01-01",
            "r1,r3,5,95,0.95,2024-01-01",
            "r3,r1,8,92,0.88,2024-01-01",
            "r2,r3,12,88,0.82,2024-01-01",
            "r3,r2,10,90,0.90,2024-01-01",
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert output["alliances"] == []


class TestHidden12GhostSponsor:
    """Did you exclude proposals with non-existent sponsors?"""

    def test_ghost_sponsor_excluded(self, tmp_path):
        reps = [{"id": "r1", "name": "A", "faction": "F", "influence": 80}]
        props = [
            {"id": "p1", "title": "Valid", "sponsor": "r1", "priority": 8},
            {"id": "p2", "title": "Ghost", "sponsor": "r_ghost", "priority": 10},
        ]
        objs = []
        rels = []
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert "p2" not in output["final_agreement"]["proposals"]
        assert "p1" in output["final_agreement"]["proposals"]


class TestHidden13MinimumViable:
    """Does it work when only 1 valid rep and proposal remain?"""

    def test_minimum_viable(self, tmp_path):
        reps = [{"id": "r1", "name": "Only", "faction": "F", "influence": 50}]
        props = [{"id": "p1", "title": "Only", "sponsor": "r1", "priority": 5}]
        objs = []
        rels = []
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert output["final_agreement"]["proposals"] == ["p1"]
        assert output["final_agreement"]["supporting_reps"] == ["r1"]
        assert output["alliances"] == []


class TestHidden14IDNormalization:
    """Did you handle mixed-case IDs across files?"""

    def test_id_normalization_across_files(self, tmp_path):
        reps = [
            {"id": "REP_001", "name": "A", "faction": "F1", "influence": 80},
            {"id": " rep_002 ", "name": "B", "faction": "F2", "influence": 70},
        ]
        props = [
            {"id": "PROP_001", "title": "Bill", "sponsor": "Rep_001", "priority": 8},
        ]
        objs = [
            {"rep_id": " REP_002 ", "proposal_id": "prop_001", "severity": 5},
        ]
        rels = ["REP_001, rep_002 ,80,20,0.1,2024-01-01",
                " rep_002 ,REP_001,75,25,0.15,2024-01-01"]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        # All IDs should be normalized
        for p in output["final_agreement"]["proposals"]:
            assert p == p.strip().lower()
        for s in output["final_agreement"]["supporting_reps"]:
            assert s == s.strip().lower()
        assert len(output["final_agreement"]["proposals"]) >= 1
        assert len(output["final_agreement"]["supporting_reps"]) >= 1


class TestHidden15DuplicateProposals:
    """Did you deduplicate correctly?"""

    def test_duplicate_proposals_deduped(self, tmp_path):
        reps = [{"id": "r1", "name": "A", "faction": "F", "influence": 80}]
        props = [
            {"id": "p1", "title": "Original", "sponsor": "r1", "priority": 8},
            {"id": "p1", "title": "Duplicate", "sponsor": "r1", "priority": 5},
            {"id": "p2", "title": "Other", "sponsor": "r1", "priority": 6},
        ]
        objs = []
        rels = []
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        proposals = output["final_agreement"]["proposals"]
        # No duplicates in output
        assert len(proposals) == len(set(proposals))
        assert proposals.count("p1") <= 1


class TestHidden16NullInfluence:
    """Does it handle missing values without crashing?"""

    def test_null_influence_no_crash(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F", "influence": None},
            {"id": "r2", "name": "B", "faction": "F", "influence": 80},
            {"id": "r3", "name": "C", "faction": "F", "influence": "high"},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = [{"rep_id": "r2", "proposal_id": "p1", "severity": None}]
        rels = ["r1,r2,,20,0.1,2024-01-01"]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert len(output["final_agreement"]["proposals"]) >= 1
        assert len(output["final_agreement"]["supporting_reps"]) >= 1


class TestHidden17ScaleCorrectness:
    """Does it make correct decisions on 50 reps, 30 proposals?"""

    def test_scale_50_reps_30_proposals(self, tmp_path):
        # Generate 50 reps
        reps = []
        for i in range(1, 51):
            reps.append({
                "id": f"rep_{i:03d}",
                "name": f"Rep {i}",
                "faction": f"F{(i % 5) + 1}",
                "influence": 50 + (i % 50),
            })

        # Generate 30 proposals
        props = []
        for i in range(1, 31):
            props.append({
                "id": f"prop_{i:03d}",
                "title": f"Proposal {i}",
                "sponsor": f"rep_{(i % 50) + 1:03d}",
                "priority": (i % 10) + 1,
            })

        # Generate some objections
        objs = []
        for i in range(1, 21):
            objs.append({
                "rep_id": f"rep_{(i*3 % 50) + 1:03d}",
                "proposal_id": f"prop_{(i % 30) + 1:03d}",
                "severity": (i % 10) + 1,
            })

        # Generate relations (some high betrayal)
        rels = []
        trojan_id = "rep_001"
        for i in range(2, 6):
            rels.append(f"rep_001,rep_{i:03d},90,5,0.85,2024-01-01")
        for i in range(2, 20):
            j = i + 1
            if j <= 50:
                rels.append(f"rep_{i:03d},rep_{j:03d},70,20,0.15,2024-01-01")
                rels.append(f"rep_{j:03d},rep_{i:03d},65,25,0.10,2024-01-01")

        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")

        start = time.time()
        output = run_pipeline(data_dir, out)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Took {elapsed:.2f}s, must be < 2s"
        assert len(output["final_agreement"]["proposals"]) >= 1
        assert len(output["final_agreement"]["supporting_reps"]) >= 1
        # Trojan should be excluded (avg betrayal 0.85)
        assert trojan_id not in output["final_agreement"]["supporting_reps"]
        # Verify valid JSON
        json_str = json.dumps(output)
        parsed = json.loads(json_str)
        assert parsed is not None


class TestHidden18DirtyCSV:
    """Does it handle bad CSV rows without breaking clean ones?"""

    def test_dirty_csv_handled(self, tmp_path):
        reps = [
            {"id": "r1", "name": "A", "faction": "F1", "influence": 80},
            {"id": "r2", "name": "B", "faction": "F2", "influence": 70},
            {"id": "r3", "name": "C", "faction": "F3", "influence": 60},
        ]
        props = [{"id": "p1", "title": "Bill", "sponsor": "r1", "priority": 8}]
        objs = []
        # Mix of clean and dirty rows
        rels = [
            "r1,r2,80,20,0.1,2024-01-01",        # clean
            "r2,r1,75,high,0.15,2024-01-01",      # dirty rivalry
            "r1,r3,,30,0.2,2024-01-01",            # null trust
            "r3,r1,65,25,1.5,2024-01-01",          # out-of-range betrayal
            "r2,r3,70,invalid_data,0.25,2024-01-01",  # dirty rivalry
        ]
        data_dir = _make_data_dir(tmp_path, reps, props, objs,
                                  "from,to,trust,rivalry,betrayal_prob,last_interaction", rels)
        out = str(tmp_path / "out.json")
        output = run_pipeline(data_dir, out)
        assert len(output["final_agreement"]["proposals"]) >= 1
        assert len(output["final_agreement"]["supporting_reps"]) >= 1
        # Output should be valid JSON
        json_str = json.dumps(output)
        assert json.loads(json_str) is not None
