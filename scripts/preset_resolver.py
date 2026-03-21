def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def resolve_constraints(profile):
    # Baseline golden wood preset
    constraints = {
        "max_tris": 100000,
        "normal_max": 0.20,
        "roughness_min": 0.45,
        "roughness_max": 0.75,
        "texture_max_px": 2048,
        "max_file_mb": 8,
    }

    # Structure -> tris
    structure = profile.get("structure")
    if structure == "thick":
        constraints["max_tris"] = 80000
    elif structure == "medium":
        constraints["max_tris"] = 100000
    elif structure == "thin":
        constraints["max_tris"] = 120000

    # Surface detail -> normals
    detail = profile.get("surface_detail")
    if detail == "smooth":
        constraints["normal_max"] = 0.15
    elif detail == "light":
        constraints["normal_max"] = 0.20
    elif detail == "detailed":
        constraints["normal_max"] = 0.25

    # Finish -> roughness
    finish = profile.get("finish")
    if finish == "matte":
        constraints["roughness_min"] = 0.45
        constraints["roughness_max"] = 0.75
    elif finish == "soft_sheen":
        constraints["roughness_min"] = 0.35
        constraints["roughness_max"] = 0.65
    elif finish == "semi_gloss":
        constraints["roughness_min"] = 0.25
        constraints["roughness_max"] = 0.50
    elif finish == "glossy":
        constraints["roughness_min"] = 0.15
        constraints["roughness_max"] = 0.35

    # Wood tone adjustment
    tone = profile.get("wood_tone")
    if tone == "dark":
        constraints["roughness_min"] += 0.05
        constraints["roughness_max"] += 0.05

    # Metal parts adjustment
    if profile.get("metal_parts") is True:
        constraints["roughness_min"] -= 0.10
        constraints["roughness_max"] -= 0.10
        constraints["normal_max"] += 0.05

    # Clamp outputs to safe ranges
    constraints["normal_max"] = clamp(constraints["normal_max"], 0.05, 0.35)
    constraints["roughness_min"] = clamp(constraints["roughness_min"], 0.05, 0.95)
    constraints["roughness_max"] = clamp(constraints["roughness_max"], 0.10, 0.98)

    # Ensure min never exceeds max
    if constraints["roughness_min"] > constraints["roughness_max"]:
        constraints["roughness_min"], constraints["roughness_max"] = (
            constraints["roughness_max"],
            constraints["roughness_min"],
        )

    return constraints
