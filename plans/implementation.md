# Plan: Phantom Consensus Implementation

> Source PRD: ./PRD.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: CLI entry point at `consensus_engine.py` with argparse
- **Schema**: Output JSON: `{ "final_agreement": { "proposals": [], "supporting_reps": [] }, "alliances": [] }`
- **Key models**: Representatives, Proposals, Objections, Relations (loaded from 4 files)
- **Thresholds**: BETRAYAL=0.3, TRUST=60, ALLIANCE_STRENGTH=40, OBJECTION_CAP=50

---

## Phase 1: Data Loading + Basic Output

**User stories**: 1, 2, 19, 20

### What to build

Parallel loading of 4 input files (representatives.json, proposals.json, objections.json, relations.csv), basic ID normalization (strip whitespace, lowercase), and output generation with valid JSON structure containing at least 1 proposal and 1 supporter.

### Acceptance criteria

- [ ] All 4 files load without errors
- [ ] IDs normalized (e.g., "REP_001" → "rep_001", " rep_004" → "rep_004")
- [ ] Output JSON is valid and matches required schema
- [ ] At least 1 proposal and 1 supporting rep in output

---

## Phase 2: Data Cleaning Layer

**User stories**: 3, 4, 5, 6, 16

### What to build

Handle null influence values (median imputation), clamp out-of-range values (influence > 100 → 100), deduplicate entities by normalized ID, filter ghost references (objections from non-existent reps), exclude proposals with non-existent sponsors.

### Acceptance criteria

- [ ] Null influence values handled without crashing
- [ ] Out-of-range influence clamped to 100
- [ ] Duplicate proposals and reps removed
- [ ] Ghost references filtered from objections
- [ ] Ghost sponsors filtered from proposals

---

## Phase 3: Feature Engineering

**User stories**: 7, 8, 9

### What to build

Compute relationship_score = trust * (1 - betrayal_prob), objection_weight = sum(severity * objector_influence) per proposal, proposal_viability = priority * (1 - normalized_controversy), faction_betrayal_avg per rep.

### Acceptance criteria

- [ ] relationship_score computed for all rep pairs
- [ ] objection_weight aggregated per proposal
- [ ] proposal_viability calculated correctly
- [ ] faction_betrayal_avg available for infiltrator detection

---

## Phase 4: Strategic Logic - Trojan & Poison Filters

**User stories**: 10, 11

### What to build

Filter out Trojan Horse representatives (betrayal_prob > 0.3) from eligible supporters, reject Poison Pill proposals (objection_weight > 50), select proposals based on viability score, select supporters who don't object to selected proposals.

### Acceptance criteria

- [ ] High-betrayal reps (>0.3) excluded from supporters
- [ ] High-objection proposals rejected
- [ ] Selected proposals have viable scores
- [ ] Supporters don't include objectors to selected proposals

---

## Phase 5: Alliance Detection

**User stories**: 12, 13, 14, 15

### What to build

Detect False Friend relationships (asymmetric trust requires bidirectional trust > 60), detect faction infiltrators (rep betrays faction members with prob > 0.5), detect bidirectional alliances only (both directions exceed ALLIANCE_STRENGTH=40), handle complete rivalry (return empty alliances).

### Acceptance criteria

- [ ] False Friends not marked as alliances
- [ ] Faction infiltrators flagged and excluded
- [ ] Only bidirectional strong alliances detected
- [ ] Empty alliances returned when complete rivalry

---

## Phase 6: Full Pipeline + Public Tests

**User stories**: 22

### What to build

Integrate all modules into consensus_engine.py, run public format validation tests, ensure all 13 public tests pass.

### Acceptance criteria

- [ ] Full pipeline executes without errors
- [ ] Output valid JSON format
- [ ] All IDs exist in input
- [ ] No duplicates in output
- [ ] At least 1 proposal and 1 supporter

---

## Phase 7: Hidden Tests Coverage

**User stories**: 23

### What to build

Handle all 18 hidden test scenarios: scale to 50+ reps/30+ proposals, minimum viable (1 rep/1 prop), ID normalization, duplicate handling, null influence, dirty CSV, cascading betrayal, alliance hijack scenarios.

### Acceptance criteria

- [ ] Handles 50+ reps, 30+ proposals in <2s
- [ ] Minimum viable edge case works
- [ ] All ID normalization scenarios handled
- [ ] All duplicate scenarios handled
- [ ] All null/edge case scenarios handled

---

## Phase 8: ReactJS Dashboard

**User stories**: 21

### What to build

ReactJS dashboard with Vite + Tailwind + Zustand + Recharts + D3.js. Visualize: proposal pipeline, rep scoreboard, alliance network graph, faction analysis, layer breakdown stats.

### Acceptance criteria

- [ ] Dashboard loads output/final_agreement.json
- [ ] Network graph displays alliances
- [ ] Charts render correctly
- [ ] Responsive layout
- [ ] No console errors

---