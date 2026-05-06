"""
Consensus Engine - Entry Point

CLI entry point that orchestrates the full pipeline:
1. Load data (data_loader)
2. Clean data (cleaner)
3. Engineer features (feature_engineer)
4. Build consensus (consensus_builder)
5. Detect alliances (alliance_detector)
6. Output JSON result + rich analysis
"""

import argparse
import json
import os
import sys
import yaml

from src.data_loader import load_all_data
from src.cleaner import clean_all_data
from src.feature_engineer import engineer_features
from src.consensus_builder import build_consensus
from src.alliance_detector import build_alliances


def load_config(config_path: str = None) -> dict:
    """
    Load thresholds from config.yaml.

    Falls back to defaults if config file is not found.
    """
    defaults = {
        "BETRAYAL": 0.3,
        "TRUST": 60,
        "ALLIANCE_STRENGTH": 40,
        "OBJECTION_CAP": 50,
        "FACTION_BETRAYAL": 0.5,
    }

    if config_path is None:
        # Look for config.yaml in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.yaml")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f)
            if cfg and "thresholds" in cfg:
                defaults.update(cfg["thresholds"])
        except Exception:
            pass  # Use defaults on any config error

    return defaults


def _build_analysis(raw_data, clean_data, features, consensus, alliance_result, config):
    """
    Build the rich analysis JSON capturing every pipeline stage.
    This powers the dashboard's full pipeline visualization.
    """
    # --- Stage 1: Raw data stats ---
    raw_stats = {
        "representatives_loaded": len(raw_data["representatives"]),
        "proposals_loaded": len(raw_data["proposals"]),
        "objections_loaded": len(raw_data["objections"]),
        "relations_loaded": len(raw_data["relations"]),
    }

    # --- Stage 2: Cleaning stats ---
    clean_stats = {
        "representatives_after": len(clean_data["representatives"]),
        "proposals_after": len(clean_data["proposals"]),
        "objections_after": len(clean_data["objections"]),
        "relations_after": len(clean_data["relations"]),
        "reps_removed": raw_stats["representatives_loaded"] - len(clean_data["representatives"]),
        "proposals_removed": raw_stats["proposals_loaded"] - len(clean_data["proposals"]),
        "objections_removed": raw_stats["objections_loaded"] - len(clean_data["objections"]),
        "relations_removed": raw_stats["relations_loaded"] - len(clean_data["relations"]),
    }

    # --- All representatives with status ---
    trojan_horses = consensus["trojan_horses"]
    infiltrators = alliance_result["infiltrators"]
    supporter_set = set(consensus["supporters"])

    all_reps = []
    for rep in clean_data["representatives"]:
        rid = rep["id"]
        status = "eligible"
        reason = ""
        if rid in trojan_horses and rid in infiltrators:
            status = "excluded"
            reason = "Trojan Horse + Faction Infiltrator"
        elif rid in trojan_horses:
            status = "excluded"
            reason = "Trojan Horse (avg betrayal > {})".format(config["BETRAYAL"])
        elif rid in infiltrators:
            status = "excluded"
            reason = "Faction Infiltrator (faction betrayal > {})".format(config["FACTION_BETRAYAL"])
        
        if rid in supporter_set:
            status = "supporter"
            reason = "Selected as supporter"

        # Compute avg outgoing betrayal
        outgoing = [float(r["betrayal_prob"]) for r in clean_data["relations"] if r["from"] == rid]
        avg_betrayal = sum(outgoing) / len(outgoing) if outgoing else 0.0

        all_reps.append({
            "id": rid,
            "name": rep.get("name", ""),
            "faction": rep.get("faction", ""),
            "influence": rep["influence"],
            "status": status,
            "reason": reason,
            "avg_betrayal": round(avg_betrayal, 3),
            "faction_betrayal_avg": round(features["faction_betrayal_avg"].get(rid, 0.0), 3),
        })

    # --- All proposals with status ---
    selected_set = set(consensus["selected_proposals"])
    all_proposals = []
    for prop in clean_data["proposals"]:
        pid = prop["id"]
        obj_weight = features["objection_weights"].get(pid, 0.0)
        viability = features["proposal_viability"].get(pid, 0.0)

        status = "selected"
        reason = "Passed all filters"
        if pid not in selected_set:
            if obj_weight > config["OBJECTION_CAP"]:
                status = "rejected"
                reason = "Poison Pill (objection_weight {:.0f} > cap {})".format(obj_weight, config["OBJECTION_CAP"])
            else:
                status = "rejected"
                reason = "Lower viability score"

        all_proposals.append({
            "id": pid,
            "title": prop.get("title", ""),
            "sponsor": prop.get("sponsor", ""),
            "priority": prop["priority"],
            "objection_weight": round(obj_weight, 1),
            "viability": round(viability, 3),
            "status": status,
            "reason": reason,
        })

    # --- All relations with scores ---
    rel_scores = features["relationship_scores"]
    all_relations = []
    for rel in clean_data["relations"]:
        fid = rel["from"]
        tid = rel["to"]
        score = rel_scores.get((fid, tid), 0.0)
        all_relations.append({
            "from": fid,
            "to": tid,
            "trust": rel["trust"],
            "rivalry": rel["rivalry"],
            "betrayal_prob": rel["betrayal_prob"],
            "relationship_score": round(score, 2),
        })

    # --- Objection details ---
    all_objections = []
    rep_influence_map = {r["id"]: r["influence"] for r in clean_data["representatives"]}
    for obj in clean_data["objections"]:
        influence = rep_influence_map.get(obj["rep_id"], 0)
        all_objections.append({
            "rep_id": obj["rep_id"],
            "proposal_id": obj["proposal_id"],
            "severity": obj["severity"],
            "influence": influence,
            "weighted_impact": round(obj["severity"] * influence, 1),
        })

    # --- Faction analysis ---
    factions = {}
    for rep in clean_data["representatives"]:
        faction = rep.get("faction", "Unknown")
        if faction not in factions:
            factions[faction] = {"members": [], "infiltrators": [], "avg_influence": 0}
        factions[faction]["members"].append(rep["id"])
        if rep["id"] in infiltrators:
            factions[faction]["infiltrators"].append(rep["id"])

    for fname, fdata in factions.items():
        influences = [
            r["influence"] for r in clean_data["representatives"]
            if r.get("faction") == fname
        ]
        fdata["avg_influence"] = round(sum(influences) / len(influences), 1) if influences else 0
        fdata["member_count"] = len(fdata["members"])

    # --- Alliance details ---
    alliance_details = []
    for pair in alliance_result["alliances"]:
        a, b = pair
        score_ab = rel_scores.get((a, b), 0.0)
        score_ba = rel_scores.get((b, a), 0.0)
        trust_ab = next((float(r["trust"]) for r in clean_data["relations"] if r["from"] == a and r["to"] == b), 0)
        trust_ba = next((float(r["trust"]) for r in clean_data["relations"] if r["from"] == b and r["to"] == a), 0)
        alliance_details.append({
            "pair": pair,
            "score_a_to_b": round(score_ab, 2),
            "score_b_to_a": round(score_ba, 2),
            "trust_a_to_b": trust_ab,
            "trust_b_to_a": trust_ba,
        })

    return {
        "config": config,
        "pipeline": {
            "raw_stats": raw_stats,
            "clean_stats": clean_stats,
        },
        "representatives": all_reps,
        "proposals": all_proposals,
        "relations": all_relations,
        "objections": all_objections,
        "factions": factions,
        "alliances": alliance_details,
        "trojan_horses": list(trojan_horses),
        "infiltrators": list(infiltrators),
    }


def run_pipeline(input_dir: str, output_file: str, config_path: str = None) -> dict:
    """
    Execute the full consensus engine pipeline.

    Args:
        input_dir: Path to the directory containing raw data files.
        output_file: Path to write the output JSON file.
        config_path: Optional path to config.yaml.

    Returns:
        The output dictionary.
    """
    # Load config
    config = load_config(config_path)

    # Phase 1: Load data
    raw_data = load_all_data(input_dir)

    # Phase 2: Clean data
    clean_data = clean_all_data(raw_data)

    # Phase 3: Engineer features
    features = engineer_features(clean_data)

    # Phase 4: Build consensus (Trojan Horse + Poison Pill filtering)
    consensus = build_consensus(
        clean_data, features,
        betrayal_threshold=config["BETRAYAL"],
        objection_cap=config["OBJECTION_CAP"],
    )

    # Phase 5: Detect alliances
    alliance_result = build_alliances(
        clean_data, features,
        trojan_horses=consensus["trojan_horses"],
        alliance_strength=config["ALLIANCE_STRENGTH"],
        trust_threshold=config["TRUST"],
        faction_betrayal_threshold=config["FACTION_BETRAYAL"],
    )

    # Phase 6: Build final output
    output = {
        "final_agreement": {
            "proposals": consensus["selected_proposals"],
            "supporting_reps": consensus["supporters"],
        },
        "alliances": alliance_result["alliances"],
    }

    # Write output
    out_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(out_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # Write rich analysis for dashboard
    analysis = _build_analysis(raw_data, clean_data, features, consensus, alliance_result, config)
    analysis_path = os.path.join(out_dir, "analysis.json")
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    return output


def main():
    """CLI entry point with argparse."""
    parser = argparse.ArgumentParser(
        description="Phantom Consensus Engine - Strategic political consensus builder"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="data/raw",
        help="Path to the directory containing raw data files (default: data/raw)",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="output/final_agreement.json",
        help="Path to write the output JSON file (default: output/final_agreement.json)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yaml (default: auto-detect)",
    )
    args = parser.parse_args()

    try:
        output = run_pipeline(args.input_dir, args.output_file, args.config)
        print(f"Consensus engine completed successfully.")
        print(f"Output written to: {args.output_file}")
        print(f"Proposals selected: {len(output['final_agreement']['proposals'])}")
        print(f"Supporting reps: {len(output['final_agreement']['supporting_reps'])}")
        print(f"Alliances detected: {len(output['alliances'])}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
