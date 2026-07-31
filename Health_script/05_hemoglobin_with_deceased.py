from health_utils import OUT, load_living_plus_deceased, print_compact_table, run_river_interaction


# Hemoglobin survivor-bias sensitivity analysis.
# Deceased children are included with an extreme hemoglobin value of -20 g/dL, matching the manuscript sensitivity design.
# OLC exposure: sustained prior-three-year OLC area within 15 km, transformed as log1p(area).
# Table S3 reports the same river scales as the survivor-only hemoglobin model.
RIVER_SCALES_KM = [1, 3, 5, 10, 15]
EXPOSURE = "log_olc_sustained_15km"
DECEASED_HB_VALUE = -20.0


def main() -> None:
    df = load_living_plus_deceased(deceased_hb_value=DECEASED_HB_VALUE)
    out = run_river_interaction(
        df=df,
        outcome="hb_level",
        exposure=EXPOSURE,
        river_scales_km=RIVER_SCALES_KM,
        include_water=True,
        river_grouping="upstream_vs_mid_down",
        model_name="hemoglobin_with_deceased_extreme_value",
        use_formula=True,
    )
    out.to_csv(OUT / "health_hemoglobin_with_deceased_results.csv", index=False)
    print_compact_table(out)
    print(f"\nSaved: {OUT / 'health_hemoglobin_with_deceased_results.csv'}")


if __name__ == "__main__":
    main()
