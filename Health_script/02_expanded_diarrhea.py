import pandas as pd

from health_utils import OUT, load_living, print_compact_table, run_river_interaction


# Expanded-sample diarrhea sensitivity analysis.
# This model omits the water-source quality covariate to reincorporate records missing that variable.
# OLC exposure uses 5 km, 10 km, and 15 km concurrent OLC intensity; river grouping matches the strict diarrhea model.
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
                include_water=False,
                river_grouping="upstream_isolated_vs_mid_down",
                model_name=f"expanded_diarrhea_{exposure_scale}km_olc",
            )
        )
    out = pd.concat(results, ignore_index=True)
    out.to_csv(OUT / "health_expanded_diarrhea_results.csv", index=False)
    print_compact_table(out)
    print(f"\nSaved: {OUT / 'health_expanded_diarrhea_results.csv'}")


if __name__ == "__main__":
    main()
