# Phantom Consensus - Progress Tracker

## Project Overview

**Problem**: Build a Strategic Consensus Engine that determines which proposals pass, which politicians support the agreement, and which are secretly allied.

**Goal**: Achieve Tier S (90-100 score) by passing all 18 hidden tests.

---

## Key Decisions Summary

### Technical Stack
- **Python tooling**: `uv` for package management
- **Data libraries**: pandas + numpy
- **Frontend**: ReactJS + Vite + Tailwind + Zustand + Recharts + D3.js (npm)
- **Testing**: pytest

### Thresholds (from config.yaml)
| Threshold | Value | Purpose |
|-----------|-------|---------|
| BETRAYAL | 0.3 | Exclude reps with betrayal_prob > 0.3 (Trojan Horse filter) |
| TRUST | 60 | Minimum bidirectional trust for alliance |
| ALLIANCE_STRENGTH | 40 | Minimum relationship_score for alliance |
| OBJECTION_CAP | 50 | Reject proposals with objection_weight > 50 (Poison Pill) |
| FACTION_BETRAYAL | 0.5 | Flag infiltrators (betrays faction > 50%) |

### Data Pipeline (Option B - Parallel Loading)
1. Load all 4 files in parallel
2. Unified ID normalization (strip whitespace, lowercase)
3. Cross-validate foreign keys
4. Clean per-file dirty data
5. Feature engineering
6. Consensus logic

### Formulas
- `relationship_score = trust * (1 - betrayal_prob)`
- `objection_weight = sum(severity * objector_influence)`
- `proposal_viability = priority * (1 - normalized_controversy)`

### Alliance Detection
- Union-Find (Disjoint Set Union) for connected components
- Bidirectional only (both A→B and B→A must exceed ALLIANCE_STRENGTH)
- Filter out Faction Infiltrators
- Return empty alliances on complete rivalry

### Output Format
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

## Files Created

| File | Purpose |
|------|---------|
| `PRD.md` | Product Requirements Document |
| `plans/implementation.md` | 8-phase implementation plan |

---

## Implementation Phases (8 total)

| Phase | Title | Status |
|-------|-------|--------|
| 1 | Data Loading + Basic Output | ✅ Complete |
| 2 | Data Cleaning Layer | ✅ Complete |
| 3 | Feature Engineering | ✅ Complete |
| 4 | Strategic Logic - Trojan & Poison Filters | ✅ Complete |
| 5 | Alliance Detection | ✅ Complete |
| 6 | Full Pipeline + Public Tests | ✅ Complete |
| 7 | Hidden Tests Coverage | ✅ Complete |
| 8 | ReactJS Dashboard | ✅ Complete |

---

## Phase Details (from plans/implementation.md)

### Phase 1: Data Loading + Basic Output
- Load 4 files in parallel, basic ID normalization, output valid JSON
- User stories: 1, 2, 19, 20

### Phase 2: Data Cleaning Layer
- Null handling, range clamping, deduplication, ghost filtering
- User stories: 3, 4, 5, 6, 16

### Phase 3: Feature Engineering
- relationship_score, objection_weight, proposal_viability, faction_betrayal_avg
- User stories: 7, 8, 9

### Phase 4: Strategic Logic - Trojan & Poison Filters
- Filter Trojan Horses, reject Poison Pills, select proposals/supporters
- User stories: 10, 11

### Phase 5: Alliance Detection
- False Friends, Faction Infiltrators, bidirectional alliances, complete rivalry
- User stories: 12, 13, 14, 15

### Phase 6: Full Pipeline + Public Tests
- Integrate all modules, pass 13 public format tests
- User story: 22

### Phase 7: Hidden Tests Coverage
- Handle all 18 hidden test scenarios
- User story: 23

### Phase 8: ReactJS Dashboard
- Visualize output with network graph, charts, etc.
- User story: 21

---

## User Stories (23 total)

1. Clean dirty data automatically
2. Normalize inconsistent IDs across files
3. Handle null influence without crashing
4. Clamp out-of-range influence values
5. Deduplicate proposals and representatives
6. Filter ghost references
7. Compute relationship_score
8. Compute objection_weight
9. Compute proposal_viability
10. Filter Trojan Horse representatives
11. Reject Poison Pill proposals
12. Detect False Friend relationships
13. Detect faction infiltrators
14. Detect bidirectional alliances only
15. Handle complete rivalry (empty alliances)
16. Exclude ghost sponsors
17. Handle minimum viable scenarios
18. Handle 50+ reps efficiently
19. Output in specific JSON format
20. At least 1 proposal and 1 supporter
21. Dashboard visualization
22. Pass all 13 public tests
23. Pass all 18 hidden tests

---

## Current State

**Status**: Phases 1-6 complete, ready for Phase 7
**Last session ended**: Phases 4-6 implemented, 146 total tests passing

---

## How to Continue

1. Start Phase 1: Run `uv add pandas numpy pyyaml` to set up Python deps
2. Create directory structure: src/, output/, tests/
3. Implement data_loader.py (parallel loading + ID normalization)
4. Implement consensus_builder.py (basic output generation)
5. Test: `python consensus_engine.py data/raw output/final_agreement.json`
6. Verify output format
7. Update progress.md to mark Phase 1 complete
8. Proceed to Phase 2

---

## Data Sample (from data/raw/)

**Dirty data examples to handle**:
- `influence`: "70" (string), null, 150 (out of range)
- IDs: "REP_001", "rep_001", " rep_004" (inconsistent casing/spacing)
- Duplicate: prop_003 appears twice, rep_001↔rep_002 relations duplicated
- Ghost: rep_099 in proposals (sponsor) and objections, doesn't exist in representatives
- Severity: "high" (string), -3 (negative), null
- Rivalry: "high" (string)
- Trust: null in relations.csv
- betrayal_prob: 1.5 (out of range, should be 0-1)