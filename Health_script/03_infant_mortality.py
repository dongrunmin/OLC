from health_utils import OUT, load_infant_mortality_risk_set, print_compact_table, run_river_interaction


# Corrected infant mortality risk-set analysis.
# Risk set: living children younger than 12 months plus deaths before age 12 months in the same survey/data year.
# OLC exposure: sustained prior-three-year OLC area within 15 km, transformed as log1p(area).
# River scales: final figure/table uses 3, 5, 10, and 15 km.
RIVER_SCALES_KM = [3, 5, 10, 15]
EXPOSURE = "log_olc_sustained_15km"


def main() -> None:
    df = load_infant_mortality_risk_set()
    out = run_river_interaction(
        df=df,
        outcome="is_dead",
        exposure=EXPOSURE,
        river_scales_km=RIVER_SCALES_KM,
        include_water=True,
        river_grouping="upstream_vs_mid_down",
        model_name="infant_mortality_corrected",
        include_wealth=False,
    )
    out.to_csv(OUT / "health_infant_mortality_results.csv", index=False)
    print_compact_table(out)
    print(f"\nSaved: {OUT / 'health_infant_mortality_results.csv'}")


if __name__ == "__main__":
    main()
