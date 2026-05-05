# Issues: Phantom Consensus

## Issue 1: Project Setup and Structure
**Labels**: `documentation`, `setup`

Initialize the project repository structure for the Phantom Consensus engine. Create the necessary directories for data ingestion, source code, and outputs. Ensure that the project uses standard organizational conventions. Provide a foundational structure that allows for clear separation between data parsing, logic execution, and result formatting. This issue does not cover implementation logic but ensures the working environment is prepared for the remaining features.

---

## Issue 2: Parse Representatives Data
**Labels**: `data-processing`

Create the functionality to read and ingest the `representatives.json` file. The input contains records for politicians, including their IDs, names, factions, and influence scores. The system must load this data reliably into memory to be referenced by the consensus engine. Ensure that the initial parsing handles the file format correctly, setting up a solid foundation for subsequent data sanitization and feature engineering tasks.

---

## Issue 3: Parse Proposals Data
**Labels**: `data-processing`

Develop the logic required to read the `proposals.json` file. This dataset includes bills being proposed, noting their IDs, titles, sponsoring representatives, and priority levels. The data should be ingested and stored in a structured format suitable for quick lookups during the evaluation phase. The parsing step should strictly focus on loading the data into the system, deferring any validation or normalization to later steps.

---

## Issue 4: Parse Objections Data
**Labels**: `data-processing`

Implement the necessary logic to ingest the `objections.json` file. The data details which representatives oppose specific proposals and assigns a severity score to their objections. Given the relational nature of this data, it must be loaded in a way that allows the consensus engine to quickly retrieve objections for any given proposal or representative. Focus solely on loading the raw JSON records accurately.

---

## Issue 5: Parse Relationships Data
**Labels**: `data-processing`

Read and load the `relations.csv` file, which maps the complex web of interactions between representatives. The dataset contains pairs of politicians, alongside their mutual trust, rivalry scores, and betrayal probabilities. Because this file uses a different format (CSV) from the others, a distinct parsing approach is required. Ensure that every row is loaded into the system so that the consensus engine has access to the full relationship graph.

---

## Issue 6: Sanitize Representative IDs
**Labels**: `data-processing`, `error-handling`

Normalize all representative IDs across all ingested datasets. The raw data contains inconsistent formatting, such as mixed case usage ("REP_001" vs "rep_001") and extraneous whitespace. The system must standardize these identifiers to ensure reliable cross-referencing between the representatives, proposals, objections, and relationship datasets. This normalization should occur before any core logic attempts to link records together.

---

## Issue 7: Handle Invalid Attribute Types
**Labels**: `error-handling`, `data-processing`

Cleanse the data attributes, specifically addressing the "influence" metric in the representatives data. The dataset intentionally includes dirty data, such as influence values formatted as strings instead of integers, null values, and out-of-bounds numbers (e.g., greater than 100). The engine must parse these safely, casting types correctly, managing missing values without crashing, and clamping or filtering out-of-range inputs.

---

## Issue 8: Deduplicate Proposals
**Labels**: `data-processing`, `error-handling`

Identify and resolve duplicate entries within the proposals dataset. The raw data may contain the same proposal multiple times, potentially with conflicting information. The system needs a defined approach to handle these duplications, ensuring that each unique proposal is only evaluated once by the consensus engine. Implement a consistent rule for deduplication that maintains the integrity of the data.

---

## Issue 9: Validate Missing References
**Labels**: `error-handling`, `data-processing`

Detect and handle missing or "ghost" references across the datasets. For instance, objections might reference a representative or a proposal that does not exist, or a proposal might be sponsored by a missing representative. The system must validate the integrity of foreign keys across all loaded data. Determine a strategy for dealing with these orphaned records, ensuring they do not disrupt the engine's processing.

---

## Issue 10: Compute Relationship Scores
**Labels**: `core-logic`, `optimization`

Derive actionable relationship scores from the raw trust and betrayal probability values. A high trust score is meaningless if the betrayal probability is also high. The system must calculate a consolidated metric that accurately reflects the reliability of a connection between two representatives. This calculated score will serve as the foundation for all subsequent alliance detection and consensus building.

---

## Issue 11: Calculate Objection Weights
**Labels**: `core-logic`

Formulate a weighted metric for each objection. The raw severity of an objection is not sufficient on its own; it must be scaled by the influence of the objecting representative. The system must calculate an aggregate objection weight for each proposal that reflects both how strongly it is opposed and how powerful the opposition is. This metric is critical for determining the viability of a proposal.

---

## Issue 12: Filter Trojan Horse Representatives
**Labels**: `core-logic`, `error-handling`

Implement logic to identify and exclude "Trojan Horse" representatives from the final agreement. These are individuals who appear highly desirable due to their large influence scores but carry an unacceptably high betrayal probability. Including them would destabilize the consensus. The engine must actively screen for these hidden risks and ensure they are not selected as supporting representatives.

---

## Issue 13: Reject Poison Pill Proposals
**Labels**: `core-logic`

Design the system to detect and avoid "Poison Pill" proposals. These are bills that might have an extremely high priority score but face severe, widespread objections from influential representatives. Selecting such a proposal would alienate supporters and collapse the agreement. The engine must weigh the proposal's priority against the calculated aggregate objection weight to determine its true viability.

---

## Issue 14: Identify Genuine Alliances
**Labels**: `core-logic`

Develop the logic necessary to detect strong, stable alliances between representatives. This requires analyzing the relationship scores across the network to find pairs or groups of politicians who reliably support one another. The engine must output these detected alliances as part of the final result. The logic must distinguish between casual connections and genuinely stable political blocks.

---

## Issue 15: Handle Asymmetric Trust
**Labels**: `core-logic`

Address scenarios involving asymmetric trust, where one representative highly trusts another, but the feeling is not mutual. These "False Friend" relationships are inherently unstable and should not be misclassified as genuine alliances. The consensus engine must evaluate relationships directionally and require mutual reliability before considering two politicians to be safely allied.

---

## Issue 16: Uncover Faction Infiltrators
**Labels**: `core-logic`, `error-handling`

Implement safeguards to detect spies or infiltrators within factions. A representative may claim membership in a specific faction but possess high betrayal probabilities against other members of that same faction. The system must not assume that shared faction labels guarantee safety. It must independently verify trust levels within factions to prevent internal sabotage of the consensus.

---

## Issue 17: Formulate Consensus Output
**Labels**: `core-logic`, `optimization`

Design the core decision-making loop that finalizes the agreement. Using all derived metrics, cleaned data, and identified relationships, the system must select the optimal set of proposals and the supporting representatives. The final outcome must represent a stable consensus that maximizes value while minimizing the risk of betrayal and overwhelming objection. 

---

## Issue 18: Format JSON Output
**Labels**: `data-processing`

Construct the final output generation module. The system must format its decisions into a specific JSON structure containing the final agreement (selected proposals and supporting representatives) and the detected alliances. Ensure the output strictly adheres to the requested schema, as any deviation will cause evaluation failures. The file should be saved consistently and cleanly.

---

## Issue 19: Handle Extreme Edge Cases
**Labels**: `error-handling`, `performance`

Ensure the system remains stable under extreme conditions, such as complete rivalry or minimal viability. If every representative is a rival, the system should correctly return empty alliances. If only one valid representative and proposal remain after cleaning, the engine must still function correctly. Validate that edge cases do not result in application crashes or infinite loops.

---

## Issue 20: Scale Performance Profiling
**Labels**: `performance`, `optimization`

Profile the consensus engine to ensure it operates efficiently with larger datasets. The system must perform correctly and quickly when scaled up to handle 50+ representatives and 30+ proposals. Optimize any bottleneck algorithms, such as nested loops over the relationship graph or redundant objection calculations. Ensure the final solution executes within reasonable time limits.
