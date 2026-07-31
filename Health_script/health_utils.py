from __future__ import annotations

import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "Health" / "outputs"
OUT.mkdir(exist_ok=True)

RIVER_SCALES_KM = [1, 2, 3, 5, 10, 15]
BUFFER_RADII_KM = [1, 5, 10, 15]

RENAME_MAP = {
    "weight_child": "sample_weight",
    "water_source": "water_source_code",
    "water_improved_binary": "water_improved",
    "cooking_fuel": "cooking_fuel_code",
    "mosquito_nets_owned": "mosquito_nets",
    "olc_dist": "olc_dist_m",
    "olc1km": "olc_count_1km",
    "olc5km": "olc_count_5km",
    "olc10km": "olc_count_10km",
    "olc15km": "olc_count_15km",
    "olc1km_avg": "olc_sustained_1km",
    "olc5km_avg": "olc_sustained_5km",
    "olc10km_avg": "olc_sustained_10km",
    "olc15km_avg": "olc_sustained_15km",
    "typ_1km": "river_type_1km",
    "typ_2km": "river_type_2km",
    "typ_3km": "river_type_3km",
    "typ_5km": "river_type_5km",
    "typ_10km": "river_type_10km",
    "typ_15km": "river_type_15km",
    "grid05_id": "grid_id_05",
    "grid01_id": "grid_id_01",
}


def stars(p_value: float) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def material_quality(code: object) -> float:
    try:
        value = int(code)
    except Exception:
        return np.nan
    if 10 <= value < 20:
        return 1.0
    if 20 <= value < 30:
        return 2.0
    if 30 <= value < 40:
        return 3.0
    return np.nan


def first_principal_component(frame: pd.DataFrame) -> np.ndarray:
    filled = frame.copy()
    for col in filled.columns:
        mode = filled[col].dropna().mode()
        fallback = float(mode.iloc[0]) if not mode.empty else 0.0
        filled[col] = filled[col].fillna(fallback)
    values = filled.values.astype(float)
    centered = values - values.mean(axis=0, keepdims=True)
    # Match the original analysis scripts: sklearn PCA centers variables but does
    # not standardize them before extracting the first housing-quality component.
    _, _, right_vectors = np.linalg.svd(centered, full_matrices=False)
    return centered @ right_vectors[0]


def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().rename(columns=RENAME_MAP)
    if "calc_age_months" in out.columns:
        out["child_age_months"] = pd.to_numeric(out["calc_age_months"], errors="coerce")

    numeric_cols = [
        "diarrhea_binary",
        "hb_level",
        "water_improved",
        "clean_fuel",
        "mosquito_nets",
        "is_wet_season",
        "child_age_months",
        "child_sex",
        "head_sex",
        "mother_edu",
        "wealth_index",
        "toilet_type",
        "interview_year",
        "grid_id_05",
        "is_dead",
    ]
    for km in BUFFER_RADII_KM:
        numeric_cols.extend([f"olc_count_{km}km", f"olc_sustained_{km}km"])
    for km in RIVER_SCALES_KM:
        numeric_cols.append(f"river_type_{km}km")
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out["child_female"] = (out.get("child_sex") == 2).astype(int)
    out["head_female"] = (out.get("head_sex") == 2).astype(int)
    if "clean_fuel" in out.columns:
        out["clean_fuel"] = out["clean_fuel"].fillna(-1)

    for col in ["floor_material", "wall_material", "roof_material"]:
        if col not in out.columns:
            out[col] = np.nan
    quality = pd.DataFrame(
        {
            "floor_quality": out["floor_material"].apply(material_quality),
            "wall_quality": out["wall_material"].apply(material_quality),
            "roof_quality": out["roof_material"].apply(material_quality),
        }
    )
    out["housing_quality_index"] = first_principal_component(quality)

    for km in BUFFER_RADII_KM:
        for exposure_type in ["count", "sustained"]:
            col = f"olc_{exposure_type}_{km}km"
            if col in out.columns and f"log_{col}" not in out.columns:
                out[f"log_{col}"] = np.log1p(pd.to_numeric(out[col], errors="coerce"))
    return out


def load_living() -> pd.DataFrame:
    return prepare_model_data(pd.read_csv(DATA / "health" / "living_children_model_ready.csv"))


def load_living_plus_deceased(deceased_hb_value: float = -20.0) -> pd.DataFrame:
    living = pd.read_csv(DATA / "health" / "living_children_model_ready.csv")
    deceased = pd.read_csv(DATA / "health" / "deceased_children_model_ready.csv")
    living["is_dead"] = 0
    deceased["is_dead"] = 1
    deceased["hb_level"] = deceased_hb_value
    combined = pd.concat([living, deceased], ignore_index=True, sort=False)
    return prepare_model_data(combined)


def load_infant_mortality_risk_set() -> pd.DataFrame:
    return prepare_model_data(pd.read_csv(DATA / "health" / "infant_mortality_model_ready.csv"))


def build_design_matrix(
    data: pd.DataFrame,
    outcome: str,
    exposure: str,
    include_water: bool,
    include_wealth: bool,
    group_col: str = "grid_id_05",
) -> tuple[pd.Series, pd.DataFrame, pd.Series, pd.DataFrame]:
    continuous = [
        exposure,
        "is_upstream",
        "child_age_months",
        "child_female",
        "head_female",
        "housing_quality_index",
        "clean_fuel",
        "mosquito_nets",
        "is_wet_season",
    ]
    if include_water:
        continuous.append("water_improved")

    categorical = ["mother_edu", "interview_year", "grid_id_05", "toilet_type"]
    if include_wealth:
        categorical.insert(1, "wealth_index")
    required = [outcome, group_col] + continuous + categorical
    required = [col for col in required if col in data.columns]
    used = data.dropna(subset=required).copy()
    used[f"{exposure}:is_upstream"] = used[exposure] * used["is_upstream"]

    x_parts = [used[continuous + [f"{exposure}:is_upstream"]].astype(float)]
    for col in categorical:
        if col in used.columns and used[col].nunique(dropna=True) > 1:
            dummies = pd.get_dummies(used[col].astype("category"), prefix=col, drop_first=True)
            x_parts.append(dummies.astype(float))
    x = pd.concat(x_parts, axis=1)
    x = sm.add_constant(x, has_constant="add")
    y = used[outcome].astype(float)
    groups = used[group_col]
    return y, x, groups, used


def fit_clustered_ols(
    data: pd.DataFrame,
    outcome: str,
    exposure: str,
    include_water: bool,
    include_wealth: bool,
    group_col: str = "grid_id_05",
):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y, x, groups, used = build_design_matrix(data, outcome, exposure, include_water, include_wealth, group_col=group_col)
        if y.nunique(dropna=True) < 2:
            raise ValueError("Outcome has no variation after formula-based missing-data handling.")
        result = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": groups})
        return result, used


def control_formula(data: pd.DataFrame, include_water: bool, include_wealth: bool) -> str:
    terms = [
        "child_age_months",
        "child_female",
        "head_female",
        "C(mother_edu)",
    ]
    if include_wealth:
        terms.append("C(wealth_index)")
    terms.append("housing_quality_index")
    if include_water:
        terms.append("water_improved")
    terms.extend(["clean_fuel", "mosquito_nets", "is_wet_season", "C(interview_year)", "C(grid_id_05)"])
    if "toilet_type" in data.columns and 1 < data["toilet_type"].nunique(dropna=True) < 20:
        terms.append("C(toilet_type)")
    return " + ".join(terms)


def fit_clustered_ols_formula(
    data: pd.DataFrame,
    outcome: str,
    exposure: str,
    include_water: bool,
    include_wealth: bool,
    group_col: str = "grid_id_05",
):
    controls = control_formula(data, include_water=include_water, include_wealth=include_wealth)
    formula = f"{outcome} ~ {exposure} * is_upstream + {controls}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = smf.ols(formula=formula, data=data)
        row_idx = model.data.row_labels
        used = data.loc[row_idx].copy()
        groups = data.loc[row_idx, group_col]
        if used[outcome].nunique(dropna=True) < 2:
            raise ValueError("Outcome has no variation after formula-based missing-data handling.")
        result = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
        return result, used


def add_result_rows(rows: list[dict], result, metadata: dict, exposure: str, interaction: str) -> None:
    used = metadata.pop("used_data")
    n_up = int((used["is_upstream"] == 1).sum())
    n_down = int((used["is_upstream"] == 0).sum())
    terms = [
        ("downstream_effect", exposure),
        ("upstream_interaction", interaction),
        ("upstream_main", "is_upstream"),
    ]
    for label, term in terms:
        rows.append(
            {
                **metadata,
                "term": label,
                "raw_term": term,
                "coef": float(result.params[term]),
                "std_error": float(result.bse[term]),
                "p_value": float(result.pvalues[term]),
                "stars": stars(float(result.pvalues[term])),
                "n_obs": int(result.nobs),
                "n_upstream_control": n_up,
                "n_downstream_exposed": n_down,
                "r2": float(getattr(result, "rsquared", np.nan)),
            }
        )

    contrast = np.zeros(len(result.params))
    contrast[list(result.params.index).index(exposure)] = 1
    contrast[list(result.params.index).index(interaction)] = 1
    test = result.t_test(contrast)
    p_value = float(test.pvalue.item())
    rows.append(
        {
            **metadata,
            "term": "net_upstream_effect",
            "raw_term": f"{exposure} + {interaction}",
            "coef": float(result.params[exposure] + result.params[interaction]),
            "std_error": float(test.sd.item()),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": int(result.nobs),
            "n_upstream_control": n_up,
            "n_downstream_exposed": n_down,
            "r2": float(getattr(result, "rsquared", np.nan)),
        }
    )


def run_river_interaction(
    df: pd.DataFrame,
    outcome: str,
    exposure: str,
    river_scales_km: Iterable[int],
    include_water: bool,
    river_grouping: str,
    model_name: str,
    include_wealth: bool = True,
    use_formula: bool = False,
) -> pd.DataFrame:
    rows: list[dict] = []
    for scale in river_scales_km:
        river_col = f"river_type_{scale}km"
        if river_grouping == "upstream_isolated_vs_mid_down":
            work = df[df[river_col].isin([0, 1, 2, 3])].copy()
            work["is_upstream"] = work[river_col].isin([0, 1]).astype(int)
        elif river_grouping == "upstream_vs_mid_down":
            work = df[df[river_col].isin([1, 2, 3])].copy()
            work["is_upstream"] = work[river_col].eq(1).astype(int)
        else:
            raise ValueError(f"Unknown river grouping: {river_grouping}")
        if work["is_upstream"].nunique(dropna=True) < 2:
            continue

        if use_formula:
            result, used = fit_clustered_ols_formula(
                work,
                outcome,
                exposure,
                include_water=include_water,
                include_wealth=include_wealth,
            )
        else:
            result, used = fit_clustered_ols(
                work,
                outcome,
                exposure,
                include_water=include_water,
                include_wealth=include_wealth,
            )
        interaction = f"{exposure}:is_upstream"
        if interaction not in result.params:
            interaction = f"is_upstream:{exposure}"
        add_result_rows(
            rows,
            result,
            {
                "model": model_name,
                "outcome": outcome,
                "scale_km": scale,
                "exposure": exposure,
                "include_water_control": include_water,
                "include_wealth_control": include_wealth,
                "river_grouping": river_grouping,
                "used_data": used,
            },
            exposure,
            interaction,
        )
    return pd.DataFrame(rows)


def print_compact_table(results: pd.DataFrame) -> None:
    if results.empty:
        print("No model results were produced.")
        return
    for (model, exposure), part in results.groupby(["model", "exposure"], sort=False):
        print(f"\n{model} | exposure={exposure}")
        print("scale_km term                   coef      se        p       n_obs  n_up  n_down")
        for _, row in part.iterrows():
            print(
                f"{int(row['scale_km']):>8} {row['term']:<22} "
                f"{row['coef']:>8.4f}{row['stars']:<3} {row['std_error']:>8.4f} "
                f"{row['p_value']:>7.3f} {int(row['n_obs']):>7} "
                f"{int(row['n_upstream_control']):>5} {int(row['n_downstream_exposed']):>7}"
            )
