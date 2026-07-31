from health_utils import OUT, load_living, print_compact_table, run_river_interaction


# Hemoglobin analysis among living children only.
# OLC exposure: sustained prior-three-year OLC area within 15 km, transformed as log1p(area).
# All river scales are exported for tables; plotting code can filter out 2 km when needed.
RIVER_SCALES_KM = [1, 3, 5, 10, 15]
EXPOSURE = "log_olc_sustained_15km"


def main() -> None:
    df = load_living()
    out = run_river_interaction(
        df=df,
        outcome="hb_level",
        exposure=EXPOSURE,
        river_scales_km=RIVER_SCALES_KM,
        include_water=True,
        river_grouping="upstream_vs_mid_down",
        model_name="hemoglobin_survivors_only",
        use_formula=True,
    )
    out.to_csv(OUT / "health_hemoglobin_survivors_results.csv", index=False)
    print_compact_table(out)
    print(f"\nSaved: {OUT / 'health_hemoglobin_survivors_results.csv'}")


if __name__ == "__main__":
    main()
