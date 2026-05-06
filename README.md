# Phantom Consensus

## Team Information
- **Team Name**: MisaMisa
- **Year**: 3rd Year
- **All-Female Team**: NO

## Architecture Overview

### 1. Data Cleaning
We built a robust pandas-based pipeline handling anomalies systematically: missing numerics were imputed or coerced to safe defaults using `pd.to_numeric`, and numeric outliers were mathematically clamped (e.g., `betrayal_prob` bound to 0-1, `influence` capped at 100). All foreign keys and identifiers passed through strict normalization (lowercase and stripped whitespace) to fix format mismatches. Finally, cross-table relational integrity checks stripped out "Ghost references" and duplicates.

### 2. Alliance Detection Logic
We utilized a Disjoint Set Union (Union-Find) algorithm to cluster representatives into connected alliances. Crucially, the logic enforces strict **bidirectional trust thresholds** (> 60) and asymmetric relationship gating (`relationship = trust * (1 - betrayal_prob)` > 40 on both sides) to immediately reject "False Friends". We also isolated "Faction Infiltrators" who betray their own faction >50% of the time.

### 3. Proposal Prioritization
Proposals are ranked using a derived **viability** metric (`priority * (1 - normalized_controversy)`). The controversy metric isn't flat; it scales dynamically as an `objection_weight`, calculated by multiplying the `severity` of the objection by the objector's total `influence` score. This ensures highly influential representatives casting severe objections naturally filter out deeply unpopular ideas regardless of their raw priority.

### 4. Consensus Strategy (Trojans & Poison Pills)
The engine runs a multi-layered exclusionary filter. A **Trojan Horse** is detected and immediately expelled if their average outgoing `betrayal_prob` across the network exceeds a strict 0.3 threshold, protecting the coalition from chronic backstabbers. A **Poison Pill** proposal is rejected outright if its total `objection_weight` exceeds a rigid cap of 50. The final agreement consists of only the most highly viable, non-poisonous proposals and a coalition composed strictly of non-Trojan supporters.

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
