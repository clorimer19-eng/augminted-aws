from dataclasses import dataclass
from typing import Any, Dict, List


HIGH_RISK_MATERIALS = {"fabric", "velvet", "leather", "fur"}
HIGH_RISK_GEOMETRY = {"soft", "organic"}


@dataclass
class Classification:
    risk: str          # LOW_RISK | HIGH_RISK
    route: str         # AUTOMATED | ASSISTED | HUMAN_OR_REJECT
    reasons: List[str]


def classify_and_route(job: Dict[str, Any]) -> Classification:
    parts = job.get("declared_parts", [])
    reasons: List[str] = []


    has_soft = any(p.get("geometry") in HIGH_RISK_GEOMETRY for p in parts)
    has_folds = any(bool(p.get("has_folds")) for p in parts)
    has_high_mat = any(p.get("material") in HIGH_RISK_MATERIALS for p in parts)


    # Olga-style: interactions matter more than single factors
    if has_high_mat and (has_soft or has_folds):
        reasons.append("High-risk interaction: high-risk material + soft/folds (automation lies here).")
        return Classification("HIGH_RISK", "ASSISTED", reasons)


    if has_high_mat:
        reasons.append("High-risk material detected (fabric/leather/velvet/fur).")
        return Classification("HIGH_RISK", "ASSISTED", reasons)


    if has_soft or has_folds:
        reasons.append("Soft geometry/folds detected (normal-vs-geometry ambiguity).")
        return Classification("HIGH_RISK", "ASSISTED", reasons)


    reasons.append("Hard-surface dominant, no high-risk materials/folds detected.")
    return Classification("LOW_RISK", "AUTOMATED", reasons)


@dataclass
class PipelineConfig:
    rembg: bool
    slicer: bool
    geometry_rules: bool
    safety_pass: bool

def get_pipeline_config(category: str) -> PipelineConfig:
    """
    Returns the pipeline flags based on the category.
    """
    # v1 Locked Scope: Rigid Furniture Only
    # Explicit Allowlist
    SUPPORTED_CATEGORIES = {
        "table", "chair", "armchair", "sofa", "sofa_bed", "bed",
        "desk", "computer_desk", "bench", "cabinet", "storage_unit",
        "wardrobe", "bookcase", "shelving_unit"
    }

    # Explicit Blocklist (Hard Reject)
    EXCLUDED_CATEGORIES = {
        "rug", "mat", "carpet", "art_canvas", "floor_lamp", "outdoor_furniture"
    }

    if category in EXCLUDED_CATEGORIES:
        raise ValueError(f"Category '{category}' is explicitly excluded from v1.")

    if category not in SUPPORTED_CATEGORIES:
        # Strict v1: Reject unknown
        raise ValueError(f"Category '{category}' is not in the v1 allowlist.")

    # v1 Pipeline Configuration
    # "rembg = False for all supported rigid furniture categories."
    # "Safety pass ON for all jobs."
    return PipelineConfig(
        rembg=False,
        slicer=False,
        geometry_rules=False,
        safety_pass=True
    )
