# Phantom Consensus - Product Requirements Document

---

## Problem Statement

Participants in the Phantom Consensus hackathon must build a Strategic Consensus Engine that acts as a political advisor. Given a messy dataset of politicians (representatives), proposals, relationships, and objections, the system must determine:

- Which proposals should be passed
- Which politicians support the agreement
- Which politicians are secretly allied with each other

The challenge is multi-layered: the input data is intentionally dirty (string vs number, nulls, out-of-range values, inconsistent IDs), requires feature engineering (relationship scores, objection weights, proposal viability), comes from 4 separate files in different formats, and contains strategic traps (Trojan Horse reps, Poison Pill proposals, False Friend relationships, Faction Infiltrators).

---

## Solution

A Python-based consensus engine that processes 4 input files through 4 layers (dirty data cleaning → feature engineering → multi-file handling → strategic logic) to produce a JSON output with selected proposals, supporting representatives, and detected alliances. Coupled with a ReactJS dashboard for visualization and analysis.

---

## User Stories

1. As a hackathon participant, I want to clean dirty data automatically, so that I can focus on strategic logic rather than data preprocessing.
2. As a system, I need to normalize inconsistent IDs across all 4 input files (e.g., "REP_001" vs "rep_001" vs " rep_001"), so that cross-referencing works correctly.
3. As a system, I need to handle null influence values without crashing, so that missing data doesn't break the pipeline.
4. As a system, I need to clamp out-of-range influence values (e.g., 150 > max 100), so that data stays within valid bounds.
5. As a system, I need to deduplicate proposals and representatives, so that each entity is evaluated only once.
6. As a system, I need to filter ghost references (objections from reps who don't exist), so that orphaned records don't disrupt processing.
7. As a system, I need to compute relationship_score = trust * (1 - betrayal_prob), so that high trust but high betrayal is correctly identified as dangerous.
8. As a system, I need to compute objection_weight = sum(severity * objector_influence) per proposal, so that powerful reps' objections carry more weight.
9. As a system, I need to compute proposal_viability = priority * (1 - normalized_controversy), so that high-priority proposals everyone hates are correctly identified as unviable.
10. As a system, I need to filter out Trojan Horse representatives (high influence but betrayal_prob > 0.3), so that dangerous candidates don't destabilize the agreement.
11. As a system, I need to reject Poison Pill proposals (high priority but total objection_weight > threshold), so that universally-opposed bills don't pass.
12. As a system, I need to detect False Friend relationships (asymmetric trust), so that one-way trust isn't misclassified as alliance.
13. As a system, I need to detect faction infiltrators (rep claims a faction but betrays members with prob > 0.5), so that spies aren't included in stable alliances.
14. As a system, I need to detect bidirectional alliances only, so that mutual reliability is required for alliance formation.
15. As a system, I need to return empty alliances when complete rivalry exists (all relationship_scores below threshold), so that edge cases are handled gracefully.
16. As a system, I need to exclude proposals with non-existent sponsors (ghost sponsors), so that invalid proposals are filtered.
17. As a system, I need to handle minimum viable scenarios (1 valid rep and 1 proposal), so that the engine doesn't crash on edge cases.
18. As a system, I need to handle 50+ representatives and 30+ proposals efficiently, so that the solution scales.
19. As a judge, I want the output in a specific JSON format with proposals, supporting_reps, and alliances, so that automated evaluation works correctly.
20. As a judge, I want at least 1 proposal and 1 supporter in output, so that trivial edge cases are rejected.
21. As a participant, I want a dashboard visualization of the consensus output, so that I can present my solution effectively.
22. As a participant, I want to pass all 13 public format tests, so that basic validation succeeds.
23. As a participant, I want to pass all 18 hidden strategic tests, so that I achieve Tier S (90-100 score).

---

## Implementation Decisions

### Modules to Build/Modify

1. **data_loader.py** (Layer 1/3)
   - Parallel loading of 4 input files (JSON/CSV)
   - Unified ID normalization (strip whitespace, lowercase)
   - Cross-file foreign key validation

2. **cleaner.py** (Layer 1)
   - Type casting for dirty attributes (string "85" → int 85)
   - Null value handling (median imputation for influence)
   - Range clamping (150 → 100)
   - Deduplication (by normalized ID, keep first)
   - Ghost reference filtering

3. **feature_engineer.py** (Layer 2)
   - relationship_score computation
   - objection_weight aggregation
   - proposal_viability scoring
   - faction_betrayal_avg calculation

4. **alliance_detector.py** (Layer 4)
   - Union-Find data structure for connected components
   - Bidirectional alliance detection
   - Faction infiltrator flagging
   - Complete rivalry handling

5. **consensus_builder.py** (Layer 4)
   - Trojan Horse filtering (betrayal_prob > 0.3)
   - Poison Pill rejection (objection_weight > 50)
   - Proposal selection based on viability
   - Supporter selection (non-objectors to selected proposals)

6. **consensus_engine.py** (Entry Point)
   - CLI with argparse (data/raw, output/final_agreement.json)
   - Default paths if no args provided
   - --help flag

7. **dashboard/** (ReactJS)
   - Vite + React 18 + Tailwind + Zustand
   - Recharts for charts, D3.js for network graph
   - Read output/final_agreement.json and render visualizations

### Technical Decisions

- Python tooling: **uv** for package management
- Data libraries: **pandas + numpy** for efficient manipulation
- Frontend: **ReactJS + Vite + Tailwind + Zustand + Recharts + D3.js**
- Threshold config: **config.yaml** with BETRAYAL=0.3, TRUST=60, ALLIANCE=40, OBJECTION_CAP=50

### API Contracts

- **Input**: 4 files in data/raw/ (representatives.json, proposals.json, objections.json, relations.csv)
- **Output**: final_agreement.json with structure:
  ```json
  {
    "final_agreement": {
      "proposals": ["prop_002", "prop_001"],
      "supporting_reps": ["rep_003", "rep_001", "rep_005"]
    },
    "alliances": [
      ["rep_001", "rep_004"],
      ["rep_002", "rep_005"]
    ]
  }
  ```

---

## Testing Decisions

### What Makes a Good Test
- Test external behavior only (output format, correctness), not implementation details
- Each module testable in isolation via mocked dependencies
- Integration test for full pipeline on sample data
- Public format validation mirrors the 13 public tests

### Modules to Test

1. **cleaner.py** - ID normalization, type casting, null handling, deduplication
2. **feature_engineer.py** - relationship_score, objection_weight, proposal_viability calculations
3. **alliance_detector.py** - bidirectional detection, infiltrator flagging, edge cases
4. **consensus_builder.py** - Trojan/Poison filtering, proposal selection logic
5. **consensus_engine.py** - full pipeline, CLI interface, output format

### Test Strategy

- Unit tests per module with pytest
- Integration test: run engine on data/raw/ → validate output structure
- Edge case tests: construct scenarios matching 18 hidden test descriptions (Trojan Horse, Poison Pill, False Friend, Faction Infiltrator, etc.)
- Performance test: validate <2s runtime for 50 reps, 30 proposals

---

## Out of Scope

- Real-time data fetching (static files only)
- External API integrations
- Database persistence
- Multi-user support
- Authentication/authorization
- Cloud deployment
- Mobile-responsive dashboard (desktop-first)
- Advanced caching/memoization beyond session scope

---

## Further Notes

- The solution must achieve Tier S (90-100) by passing all 18 hidden tests
- Dashboard is required but serves as tiebreaker - not directly scored
- Naive AI solutions score ~35/100 - the problem is designed to be AI-resistant
- No single correct answer exists - strategic thinking is rewarded over formula-following
- All 4 input files share the same format in hidden tests (different data, same structure)

---

**PRD complete. Ready for implementation upon approval.**