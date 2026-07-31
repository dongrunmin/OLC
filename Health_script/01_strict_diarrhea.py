import pandas as pd

from health_utils import OUT, load_living, print_compact_table, run_river_interaction


# Strict complete-case diarrhea analysis.
# River scale: assigns communities using river proximity thresholds from 1 to 15 km.
# OLC exposure: concurrent OLC area within 5 km, 10 km, and 15 km, transformed as log1p(area).
# Water-source quality is included, so observations missing this variable are dropped by the model formula.
RIVER_SCALES_KM = [1, 2, 3, 5, 10, 15]
EXPOSURE_SCALES_KM = [5, 10, 15]


def main() -> None:
    df = load_living()
    results = []
    for exposure_scale in EXPOSURE_SCALES_KM:
        results.append(
            run_river_interaction(
                df=df,
                outcome="diarrhea_binary",
                exposure=f"log_olc_count_{exposure_scale}km",
                river_scales_km=RIVER_SCALES_KM,
                include_water=True,
                river_grouping="upstream_isolated_vs_mid_down",
                model_name=f"strict_diarrhea_{exposure_scale}km_olc",
            )
        )
    out = pd.concat(results, ignore_index=True)
    out.to_csv(OUT / "health_strict_diarrhea_results.csv", index=False)
    print_compact_table(out)
    print(f"\nSaved: {OUT / 'health_strict_diarrhea_results.csv'}")


if __name__ == "__main__":
    main()
