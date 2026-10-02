"""Shared model specifications for the OLC health analyses.

Input is the combined feature-ready child CSV. Outcome-specific samples are
constructed here. No DHS extraction or GIS feature generation is performed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "health"
OUT = ROOT / "Health" / "outputs"
RIVER_SCALES_KM = (1, 2, 3, 5, 10, 15)
EXPOSURE_SCALES_KM = (5, 10, 15)
RIPARIAN_SCALES_KM = (3, 5, 10, 15)
ALIASES = {
    "weight_child": "sample_weight", "water_source": "water_source_code",
    "water_improved_binary": "water_improved", "cooking_fuel": "cooking_fuel_code",
    "mosquito_nets_owned": "mosquito_nets", "intervie_1": "interview_year",
    "grid05_id": "grid_id_05", "calc_age_months": "child_age_months",
    **{f"typ_{k}km": f"river_type_{k}km" for k in RIVER_SCALES_KM},
}
RESULT_COLUMNS = [
    "model", "outcome", "scale_km", "exposure", "weighted", "include_water",
    "include_wealth", "term", "coef", "std_error", "p_value", "stars",
    "n_obs", "n_upstream", "n_downstream",
]


def stars(p):
    return "***" if p < .01 else "**" if p < .05 else "*" if p < .1 else ""


def _quality(value):
    if pd.isna(value):
        return np.nan
    code = float(value)
    return 1.0 if 10 <= code < 20 else 2.0 if 20 <= code < 30 else 3.0 if 30 <= code < 40 else np.nan


def canonicalize(df):
    """Coalesce partial aliases, checking that overlapping values agree."""
    out = df.copy()
    for alias, target in ALIASES.items():
        if alias not in out:
            continue
        if target not in out:
            out[target] = out[alias]
        else:
            both = out[alias].notna() & out[target].notna()
            a = pd.to_numeric(out.loc[both, alias], errors="raise")
            b = pd.to_numeric(out.loc[both, target], errors="raise")
            if not np.allclose(a, b, rtol=0, atol=1e-10):
                raise ValueError(f"Conflicting columns: {alias} and {target}")
            out[target] = out[target].fillna(out[alias])
    return out


def prepare(df, *, fill_missing_fuel=True):
    """Construct controls and logs on the supplied analysis population.

    Housing PCA is fitted on the population passed by the caller. Diarrhea
    preparation uses living records. Both Hb analyses use the combined
    population so their housing index has the same fitted basis. Mortality
    also uses the combined population. Regression complete-case selection
    follows this construction.
    """
    out = canonicalize(df)
    cols = ["sample_weight", "child_age_months", "child_sex", "head_sex",
            "mother_edu", "wealth_index", "water_improved", "clean_fuel",
            "mosquito_nets", "is_wet_season", "toilet_type", "interview_year",
            "grid_id_05", "is_dead", "diarrhea_binary", "hb_level"]
    cols += [f"river_type_{k}km" for k in RIVER_SCALES_KM]
    cols += [f"olc_{prefix}_km2_{k}km" for prefix in ("area", "mean_area") for k in EXPOSURE_SCALES_KM]
    for col in cols:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="raise")
    for source, target in (("child_sex", "child_female"), ("head_sex", "head_female")):
        # Missing sex must remain missing, not become the male reference class.
        out[target] = out[source].eq(2).astype(float).where(out[source].isin([1, 2]))
    if fill_missing_fuel:
        out["clean_fuel"] = out["clean_fuel"].fillna(-1)
    q = pd.DataFrame({c: out[c].map(_quality) for c in ("floor_material", "wall_material", "roof_material")})
    if not q.notna().any().all():
        raise ValueError("Housing PCA requires an observed category in each material column")
    out["housing_quality_index"] = PCA(n_components=1).fit_transform(
        SimpleImputer(strategy="most_frequent").fit_transform(q))[:, 0]
    for k in EXPOSURE_SCALES_KM:
        for prefix in ("area", "mean_area"):
            raw = f"olc_{prefix}_km2_{k}km"
            target = f"log_olc_{prefix}_km2_{k}km"
            if raw not in out:
                continue
            if (out[raw].dropna() < 0).any():
                raise ValueError(f"Negative OLC area in {raw}")
            derived = np.log1p(out[raw])
            if target in out:
                stored = pd.to_numeric(out[target], errors="raise")
                both = stored.notna() & derived.notna()
                if not np.allclose(stored[both], derived[both], rtol=1e-10, atol=1e-12):
                    raise ValueError(f"{target} does not equal log1p({raw})")
            out[target] = derived
    return out


def _read(path=None):
    path = Path(path) if path else DATA / "all_living_and_deceased_model_ready.csv"
    df = pd.read_csv(path)
    if not df["is_dead"].isin([0, 1]).all():
        raise ValueError("is_dead must contain only 0 and 1")
    return df


def load_living(path=None, *, diarrhea=False):
    raw = _read(path)
    # Both Hb panels use the housing PCA fitted on the same combined population.
    # Only the regression sample is restricted to survivors for Panel A.
    # Keep diarrhea's existing PCA population unchanged.
    population = raw.loc[raw.is_dead.eq(0)].copy() if diarrhea else raw
    out = prepare(population)
    out = out.loc[out.is_dead.eq(0)].copy()
    if diarrhea:
        out = out.loc[out.interview_year.eq(2018)].copy()
    return out


def load_combined(path=None, *, deceased_hb=0.0):
    out = prepare(_read(path))
    # This assignment is local to the sensitivity model. Do not modify source Hb.
    out.loc[out.is_dead.eq(1), "hb_level"] = deceased_hb
    return out


def load_infant_mortality(path=None):
    out = prepare(_read(path))
    # For a deceased child this is elapsed age from birth to interview, not b7.
    return out.loc[out.child_age_months.ge(0) & out.child_age_months.lt(12)
                   & out.interview_year.isin([2018, 2021])].copy()


def _formula(outcome, exposure, water, wealth):
    controls = ["child_age_months", "child_female", "head_female", "C(mother_edu)"]
    if wealth:
        controls.append("C(wealth_index)")
    controls.append("housing_quality_index")
    if water:
        controls.append("water_improved")
    controls += ["clean_fuel", "mosquito_nets", "is_wet_season",
                 "C(interview_year)", "C(grid_id_05)", "C(toilet_type)"]
    return f"{outcome} ~ {exposure} * is_upstream + " + " + ".join(controls)


def run_river_interaction(df, outcome, exposure, river_scales_km, *,
                          include_water, include_wealth=True, weighted=True,
                          grouping="upstream_isolated_vs_mid_down", model_name="model"):
    rows, audits = [], []
    for scale in river_scales_km:
        col = f"river_type_{scale}km"
        work = df.loc[df[col].isin([0, 1, 2, 3])].copy()
        if grouping == "upstream_vs_mid_down":
            work = work.loc[work[col].isin([1, 2, 3])].copy()
            work["is_upstream"] = work[col].eq(1).astype(int)
        elif grouping == "upstream_isolated_vs_mid_down":
            work["is_upstream"] = work[col].isin([0, 1]).astype(int)
        else:
            raise ValueError(f"Unknown grouping: {grouping}")
        n_river = len(work)
        # Weighted and unweighted sensitivity fits use the same eligible sample.
        work = work.loc[np.isfinite(work.sample_weight) & work.sample_weight.gt(0)].copy()
        formula = _formula(outcome, exposure, include_water, include_wealth)
        # Discover complete cases, then rebuild the formula design on those rows.
        # Otherwise unused categorical levels inflate the cluster correction.
        probe = smf.ols(formula, data=work, missing="drop")
        used = work.loc[probe.data.row_labels].copy()
        if used[outcome].nunique() < 2 or used.is_upstream.nunique() < 2:
            raise ValueError(f"{model_name}, {scale} km: insufficient outcome/group variation")
        if used.grid_id_05.nunique() < 2:
            raise ValueError(f"{model_name}, {scale} km: fewer than two clusters")
        model = (smf.wls(formula, data=used, weights=used.sample_weight / 1_000_000,
                         missing="raise") if weighted else
                 smf.ols(formula, data=used, missing="raise"))
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": used.grid_id_05})
        interaction = f"{exposure}:is_upstream"
        names = list(fit.params.index)

        def add(label, coef, se, p):
            rows.append(dict(model=model_name, outcome=outcome, scale_km=scale,
                             exposure=exposure, weighted=weighted,
                             include_water=include_water, include_wealth=include_wealth,
                             term=label, coef=float(coef), std_error=float(se),
                             p_value=float(p), stars=stars(float(p)), n_obs=int(fit.nobs),
                             n_upstream=int(used.is_upstream.sum()),
                             n_downstream=int(used.is_upstream.eq(0).sum())))

        add("downstream_effect", fit.params[exposure], fit.bse[exposure], fit.pvalues[exposure])
        add("upstream_interaction", fit.params[interaction], fit.bse[interaction], fit.pvalues[interaction])
        contrast = np.zeros(len(names))
        contrast[names.index(exposure)] = contrast[names.index(interaction)] = 1
        test = fit.t_test(contrast)
        add("net_upstream_effect", fit.params[exposure] + fit.params[interaction],
            test.sd.item(), test.pvalue.item())
        audits.append(dict(model=model_name, scale_km=scale, weighted=weighted,
                           n_candidate=len(df), n_river=n_river, n_obs=len(used),
                           n_deceased=int(used.is_dead.sum()), n_surviving=int(used.is_dead.eq(0).sum()),
                           n_2018=int(used.interview_year.eq(2018).sum()),
                           n_2021=int(used.interview_year.eq(2021).sum()),
                           n_grid_cells=used.grid_id_05.nunique(),
                           n_design_columns=len(names), design_rank=int(np.linalg.matrix_rank(model.exog)),
                           formula=formula))
    result = pd.DataFrame(rows, columns=RESULT_COLUMNS)
    result.attrs["sample_audit"] = audits
    return result


def analysis(name, path=None):
    """Single source of configuration for the five entry scripts and runner."""
    if name in ("strict_diarrhea", "expanded_diarrhea"):
        df = load_living(path, diarrhea=True)
        parts = []
        for weighted in (True, False):
            for radius in (10, 15):
                label = f"{name}_{radius}km_olc" + ("" if weighted else "_unweighted")
                parts.append(run_river_interaction(
                    df, "diarrhea_binary", f"log_olc_area_km2_{radius}km", RIVER_SCALES_KM,
                    include_water=name == "strict_diarrhea", include_wealth=True,
                    weighted=weighted, model_name=label))
    else:
        if name == "infant_mortality":
            df, outcome, water, wealth = load_infant_mortality(path), "is_dead", False, False
        elif name == "hemoglobin_survivors":
            df, outcome, water, wealth = load_living(path), "hb_level", True, True
        elif name == "hemoglobin_with_deceased":
            df, outcome, water, wealth = load_combined(path), "hb_level", True, True
        else:
            raise ValueError(name)
        parts = [run_river_interaction(
            df, outcome, "log_olc_mean_area_km2_15km", RIPARIAN_SCALES_KM,
            include_water=water, include_wealth=wealth, weighted=True,
            grouping="upstream_vs_mid_down", model_name=name)]
    audits = [row for part in parts for row in part.attrs["sample_audit"]]
    # Clear attrs before concatenation because pandas compares attrs objects.
    for part in parts:
        part.attrs.clear()
    result = pd.concat(parts, ignore_index=True)
    result.attrs["sample_audit"] = audits
    return result


FILES = {
    "strict_diarrhea": "health_strict_diarrhea_results.csv",
    "expanded_diarrhea": "health_expanded_diarrhea_results.csv",
    "infant_mortality": "health_infant_mortality_results.csv",
    "hemoglobin_survivors": "health_hemoglobin_survivors_results.csv",
    "hemoglobin_with_deceased": "health_hemoglobin_with_deceased_results.csv",
}


def arguments(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--data", type=Path, default=DATA / "all_living_and_deceased_model_ready.csv")
    parser.add_argument("--output-dir", type=Path, default=OUT)
    return parser.parse_args()


def save_and_print(result, name, output_dir=OUT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / name, index=False)
    audits = result.attrs.get("sample_audit", [])
    if audits:
        pd.DataFrame(audits).to_csv(output_dir / name.replace(".csv", "_sample_audit.csv"), index=False)
    print(result.to_string(index=False))
    print(f"Saved: {output_dir / name}")


def run_one(name):
    args = arguments(f"Run {name} from the combined model-ready CSV")
    save_and_print(analysis(name, args.data), FILES[name], args.output_dir)
