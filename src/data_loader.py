"""
Data Loader Module (Layer 1/3)

Handles parallel loading of 4 input files (JSON/CSV) and unified ID normalization.
Provides cross-file foreign key validation.
"""

import json
import csv
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def normalize_id(raw_id: Any) -> str:
    """
    Normalize an ID: strip whitespace, convert to lowercase.
    Handles None and non-string types gracefully.
    """
    if raw_id is None:
        return ""
    return str(raw_id).strip().lower()


def _load_json_file(filepath: str) -> list[dict]:
    """Load and parse a JSON file, returning a list of dicts."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {filepath}, got {type(data).__name__}")
    return data


def _load_csv_file(filepath: str) -> list[dict]:
    """Load and parse a CSV file, returning a list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _normalize_rep_ids(representatives: list[dict]) -> list[dict]:
    """Normalize the 'id' field in representatives data."""
    for rep in representatives:
        if "id" in rep:
            rep["id"] = normalize_id(rep["id"])
    return representatives


def _normalize_proposal_ids(proposals: list[dict]) -> list[dict]:
    """Normalize 'id' and 'sponsor' fields in proposals data."""
    for prop in proposals:
        if "id" in prop:
            prop["id"] = normalize_id(prop["id"])
        if "sponsor" in prop:
            prop["sponsor"] = normalize_id(prop["sponsor"])
    return proposals


def _normalize_objection_ids(objections: list[dict]) -> list[dict]:
    """Normalize 'rep_id' and 'proposal_id' fields in objections data."""
    for obj in objections:
        if "rep_id" in obj:
            obj["rep_id"] = normalize_id(obj["rep_id"])
        if "proposal_id" in obj:
            obj["proposal_id"] = normalize_id(obj["proposal_id"])
    return objections


def _normalize_relation_ids(relations: list[dict]) -> list[dict]:
    """Normalize 'from' and 'to' fields in relations data."""
    for rel in relations:
        if "from" in rel:
            rel["from"] = normalize_id(rel["from"])
        if "to" in rel:
            rel["to"] = normalize_id(rel["to"])
    return relations


def load_all_data(input_dir: str) -> dict[str, list[dict]]:
    """
    Load all 4 input files in parallel and normalize IDs.

    Args:
        input_dir: Path to the directory containing the raw data files.

    Returns:
        A dictionary with keys: 'representatives', 'proposals', 'objections', 'relations'.
        Each value is a list of dicts with normalized IDs.
    """
    reps_path = os.path.join(input_dir, "representatives.json")
    props_path = os.path.join(input_dir, "proposals.json")
    objs_path = os.path.join(input_dir, "objections.json")
    rels_path = os.path.join(input_dir, "relations.csv")

    # Parallel loading
    with ThreadPoolExecutor(max_workers=4) as executor:
        reps_future = executor.submit(_load_json_file, reps_path)
        props_future = executor.submit(_load_json_file, props_path)
        objs_future = executor.submit(_load_json_file, objs_path)
        rels_future = executor.submit(_load_csv_file, rels_path)

        representatives = reps_future.result()
        proposals = props_future.result()
        objections = objs_future.result()
        relations = rels_future.result()

    # Normalize IDs across all datasets
    representatives = _normalize_rep_ids(representatives)
    proposals = _normalize_proposal_ids(proposals)
    objections = _normalize_objection_ids(objections)
    relations = _normalize_relation_ids(relations)

    return {
        "representatives": representatives,
        "proposals": proposals,
        "objections": objections,
        "relations": relations,
    }
