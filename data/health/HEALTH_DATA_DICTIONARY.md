# Health model-ready data dictionary

## File and survey coverage

`all_living_and_deceased_model_ready.csv` contains **7,162 rows and 82 columns**. Rows are retained in their original order. There are 6,795 living records (4,782 in 2018 and 2,013 in 2021) and 367 deceased records (322 in 2018 and 45 in 2021). Sources are the 2018 Nigeria DHS and the 2021 Nigeria MIS. No exact duplicate rows were found. Nonmissing `record_id` values are unique among living records, and `public_row_id` values are unique among deceased records.

Blank cells indicate missing values. `riv_dist = -999` denotes an unclassified river connection. Survey-cluster coordinates are displaced coordinates, not household locations. Source biomarker and symptom fields are retained for provenance. Models use the prepared outcomes and controls specified below.

## Sample construction

- **Complete-case diarrhea:** living records interviewed in 2018 with observed `diarrhea_binary` and all formula variables, including `water_improved` and wealth. N = 619 at each river scale.
- **Expanded diarrhea:** same outcome and controls, omitting only `water_improved`. Wealth is retained. N = 4,765 at each river scale.
- **Mortality:** apply `0 <= child_age_months < 12` to both living and deceased records from 2018 and 2021. The candidate cohort contains 1,367 records, including 71 deaths (59 from 2018 and 12 from 2021), before the river-connected restriction. For deceased children, age is elapsed time from birth to interview. It matches the supplied birth/interview year-month interval for all 367 deceased records. The CSV contains no `b7` or death-date field. This construction estimates recorded death in a recent-birth cohort and excludes earlier birth cohorts.
- **Survivor-only Hb:** living records with observed `hb_level` and complete included controls, including water source and wealth. The mortality age filter is not applied.
- **Mortality-inclusive Hb sensitivity:** survivors with observed Hb plus eligible deceased records assigned Hb = 0 g/dL during model preparation. Water source and wealth remain included. The source CSV retains missing Hb for all deceased records. The assigned zero is an analytical assumption, not a measured biomarker or an imputation of a deceased child's physiological Hb.

| River scale | Mortality N (up / down) | Deaths | Survivor-only Hb N (up / down) | Mortality-inclusive Hb N (up / down) | Hb deaths |
|---|---|---:|---|---|---:|
| 3 km | 224 (55 / 169) | 5 | 160 (41 / 119) | 167 (41 / 126) | 7 |
| 5 km | 325 (79 / 246) | 10 | 206 (55 / 151) | 213 (55 / 158) | 7 |
| 10 km | 478 (137 / 341) | 18 | 322 (93 / 229) | 333 (95 / 238) | 11 |
| 15 km | 568 (170 / 398) | 24 | 358 (108 / 250) | 373 (112 / 261) | 15 |

Diarrhea models use upstream plus isolated records as the comparison group. Mortality and Hb models exclude isolated records. Midstream and downstream form the exposed group throughout.

## Exposure and covariates

OLC area fields use km² and the supplied polygon-buffer intersection features. The concurrent exposure is used for acute diarrhea, while the preceding-three-year mean is used to represent sustained community contamination for mortality and Hb. Regression intensity is `ln(1 + area)`. The model-stage scripts validate logs and derive them from raw area. They do not generate or independently verify the annual spatial features or their temporal windows. OLC aggregation radii and river-proximity thresholds are different settings.

The water feature is a study-specific classification of reported source facilities. Codes 11, 12, 13, 31, 41, 61, 62, and 71 receive 1. Codes 32 and 42 receive 0. Every other observed code remains unclassified. There are 907 records coded 1, 281 coded 0, and 5,974 unclassified records. The variable name `water_improved` is retained for code compatibility and does not denote measured water quality or a complete standard improved-water classification.

Housing quality is constructed during modeling from floor, wall, and roof codes grouped into 10–19, 20–29, and 30–39, scored 1, 2, and 3. Other values are treated as missing and mode-imputed before extracting the first principal component. PCA is fitted on all living records for living-only analyses and on all combined records for mortality and combined Hb, before formula complete-case filtering. Missing child or household-head sex remains missing. The existing missing-fuel handling is retained: all model preparation assigns −1 to missing `clean_fuel`. One of these records enters the expanded diarrhea analysis, maintaining N = 4,765. These transformations are not written into the source CSV.

All models include child age, child sex, household-head sex, maternal education, housing quality, clean fuel, mosquito-net ownership, wet season, toilet categories, and 0.5° grid fixed effects. Diarrhea and Hb include wealth. Complete-case diarrhea and both Hb models include water source. Mortality excludes wealth and water source. Pooled mortality and Hb models include survey-year effects. Maternal education, wealth, toilet, grid, and year are categorical terms. Other included controls are linear terms or binary indicators.

`sample_weight` contains the DHS individual weight assigned through the interviewed mother. Weighted models minimize the sum of squared residuals multiplied by `sample_weight / 1,000,000`. The same positive-weight eligibility rule applies to the unweighted diarrhea comparisons. No additional between-survey rescaling is applied. Standard errors are clustered by `grid_id_05`, with the statsmodels finite-sample cluster correction. Complete cases are identified first, and the categorical design is then rebuilt on those records.

## Column normalization

The original combined export had 91 columns. Nine aliases were removed after checking agreement: `typ_1km`, `typ_2km`, `typ_3km`, `typ_5km`, `typ_10km`, `typ_15km`, `water_improved_core`, `water_source`, and `calc_age_months`. Their canonical fields remain. `water_source_code` was filled for 6,795 living records from `water_source`. Each of the six OLC log fields was filled for 6,795 living records from its raw area. `survey_type` was completed for 367 deceased records, and water labels were standardized. No source model values, rows, or observed outcomes were removed or replaced. The cleaning script checks consistency and writes a JSON report.

## Complete variable inventory

Availability counts below refer to the source CSV before outcome-specific selection or in-memory sensitivity assignment. `health_variable_dictionary.csv` provides the same inventory in machine-readable form.

| Variable | Group | Description | Units or coding | Nonmissing living | Nonmissing deceased |
|---|---|---|---|---:|---:|
| `DHSCLUST` | Identifier | Cluster identifier retained from the GPS linkage. | ID | 6795 | 367 |
| `LATNUM` | Spatial | Displaced survey-cluster latitude. | WGS84 degrees | 6795 | 367 |
| `LONGNUM` | Spatial | Displaced survey-cluster longitude. | WGS84 degrees | 6795 | 367 |
| `age_months_b19` | Age provenance | Recorded living-child age in months. Equals child_age_months for all living records in this release. | Months | 6795 | 0 |
| `age_months_cmc` | Age provenance | Living-child age derived from interview and birth century-month codes. May differ slightly from the recorded age. | Months | 6795 | 0 |
| `anemia_severe` | Outcome | Study-derived indicator based on Hb < 8.0 g/dL. Retained for provenance and not modeled by these five scripts. | 0/1, missing if Hb missing | 3586 | 0 |
| `birth_cmc` | Time provenance | Birth century-month code, retained for living records. | DHS century-month code | 6795 | 0 |
| `birth_history_index` | Identifier | Birth-history position for living records. | Index | 6795 | 0 |
| `birth_month` | Time | Birth month. | 1–12 | 6795 | 367 |
| `birth_year` | Time | Birth year. | Year | 6795 | 367 |
| `child_age_months` | Age | Living-child recorded age at interview. For deceased records, elapsed months from birth to interview, calculated from calendar year/month. This is not age at death. | Months | 6795 | 367 |
| `child_age_years_b8` | Age provenance | Living-child age in completed years retained from the recode. | Years | 6795 | 0 |
| `child_alive` | Outcome | Survival status. Equals 1 - is_dead. | 1 = alive, 0 = deceased | 6795 | 367 |
| `child_line_number` | Identifier | Living-child household roster line number as supplied. Deceased records have no roster line. | ID | 6795 | 0 |
| `child_sex` | Control | Child sex. | 1 = male, 2 = female | 6795 | 367 |
| `clean_fuel` | Control | Prepared clean-cooking-fuel indicator. Retained without recoding raw fuel across surveys. | 0/1, 3 missing records | 6792 | 367 |
| `cluster_id` | Identifier | Survey cluster identifier. Use together with interview_year when pooling surveys. | ID | 6795 | 367 |
| `cooking_fuel` | Control provenance | Reported cooking-fuel category from the survey-specific recode. | Categorical code | 6795 | 367 |
| `cough_binary` | Other outcome | Prepared recent cough indicator. Not used by these five scripts. | 0/1 | 4771 | 0 |
| `diarrhea_binary` | Outcome | Prepared report of diarrhea in the preceding two weeks. Available only in 2018 living records. | 0/1 | 4765 | 0 |
| `diarrhea_module_available` | Survey provenance | Indicator of diarrhea-module availability in living records. | 0/1 | 6795 | 0 |
| `fever_binary` | Other outcome | Prepared recent fever indicator. Not used by these five scripts. | 0/1 | 6774 | 0 |
| `floor_material` | Control | Floor-material source category used to construct housing PCA. | DHS categorical code | 6795 | 367 |
| `grid_id_01` | Spatial | 0.1° × 0.1° grid identifier, retained but not used by these models. | ID | 6795 | 367 |
| `grid_id_05` | Spatial control | 0.5° × 0.5° grid identifier for fixed effects and clustered standard errors. | ID | 6795 | 367 |
| `had_cough` | Outcome provenance | Original cough response. Prepared cough_binary is used for outcome analysis. | Observed 0, 2, 8 | 4782 | 0 |
| `had_diarrhea` | Outcome provenance | Original diarrhea response. Prepared diarrhea_binary is used for outcome analysis. | Observed 0, 2, 8 | 4782 | 0 |
| `had_fever` | Outcome provenance | Original fever response. Prepared fever_binary is used for outcome analysis. | Observed 0, 1, 8 | 6795 | 0 |
| `haemoglobin_adj` | Outcome provenance | Source adjusted Hb. Final hb_level equals this value divided by 10 for records with observed model Hb. | 0.1 g/dL source scale | 3586 | 0 |
| `haemoglobin_raw` | Outcome provenance | Original unadjusted Hb field, including source values not retained in final model Hb. | 0.1 g/dL source scale | 3695 | 0 |
| `haz_score` | Other outcome | Prepared height-for-age z-score. | Z-score | 2046 | 0 |
| `hb_level` | Outcome | Final adjusted Hb for survivors. Missing for all deceased records. Sensitivity assignment is performed in memory only. | g/dL | 3586 | 0 |
| `hb_level_raw` | Outcome provenance | Unadjusted Hb converted to g/dL for records retained in final Hb processing. | g/dL | 3586 | 0 |
| `head_sex` | Control | Household-head sex. | 1 = male, 2 = female | 6795 | 367 |
| `household_id` | Identifier | Household number within survey cluster. | ID | 6795 | 367 |
| `interview_cmc` | Time provenance | Interview century-month code, retained for living records. | DHS century-month code | 6795 | 0 |
| `interview_day` | Time | Interview day. | 1–31 | 6795 | 367 |
| `interview_month` | Time | Interview month. | 1–12 | 6795 | 367 |
| `interview_year` | Time control | Interview year used for cohort selection and year fixed effects. | 2018 or 2021 | 6795 | 367 |
| `is_dead` | Outcome | Recorded death status. | 1 = deceased, 0 = alive | 6795 | 367 |
| `is_wet_season` | Control | Prepared wet-season indicator. | 0 = dry, 1 = wet | 6795 | 367 |
| `log_olc_area_km2_10km` | Exposure | Natural logarithm of 1 + olc_area_km2_10km. | ln(1 + area in km²) | 6795 | 367 |
| `log_olc_area_km2_15km` | Exposure | Natural logarithm of 1 + olc_area_km2_15km. | ln(1 + area in km²) | 6795 | 367 |
| `log_olc_area_km2_5km` | Exposure | Natural logarithm of 1 + olc_area_km2_5km. | ln(1 + area in km²) | 6795 | 367 |
| `log_olc_mean_area_km2_10km` | Exposure | Natural logarithm of 1 + olc_mean_area_km2_10km. | ln(1 + area in km²) | 6795 | 367 |
| `log_olc_mean_area_km2_15km` | Exposure | Natural logarithm of 1 + olc_mean_area_km2_15km. | ln(1 + area in km²) | 6795 | 367 |
| `log_olc_mean_area_km2_5km` | Exposure | Natural logarithm of 1 + olc_mean_area_km2_5km. | ln(1 + area in km²) | 6795 | 367 |
| `mosquito_nets` | Control | Prepared household mosquito-net ownership indicator. | 0/1 | 6795 | 367 |
| `mother_edu` | Control | Maternal education, entered categorically. | 0 = none, 1 = primary, 2 = secondary, 3 = higher | 6795 | 367 |
| `mother_line_number` | Identifier | Interviewed mother’s household roster line. | ID | 6795 | 367 |
| `olc_area_km2_10km` | Exposure | Supplied current-year OLC intersection area within 10 km of the survey cluster. | km² | 6795 | 367 |
| `olc_area_km2_15km` | Exposure | Supplied current-year OLC intersection area within 15 km of the survey cluster. | km² | 6795 | 367 |
| `olc_area_km2_5km` | Exposure | Supplied current-year OLC intersection area within 5 km of the survey cluster. | km² | 6795 | 367 |
| `olc_dist` | Spatial provenance | Supplied distance to the nearest OLC feature. Not used by these five models. | Meters | 6795 | 367 |
| `olc_mean_area_km2_10km` | Exposure | Supplied mean OLC intersection area over the preceding three-year exposure window within 10 km. | km² | 6795 | 367 |
| `olc_mean_area_km2_15km` | Exposure | Supplied mean OLC intersection area over the preceding three-year exposure window within 15 km. | km² | 6795 | 367 |
| `olc_mean_area_km2_5km` | Exposure | Supplied mean OLC intersection area over the preceding three-year exposure window within 5 km. | km² | 6795 | 367 |
| `owns_land` | Other covariate | Prepared agricultural-land ownership indicator. Not used by these models. | 0/1 | 6795 | 367 |
| `owns_livestock` | Other covariate | Prepared livestock ownership indicator. Not used by these models. | 0/1 | 6795 | 367 |
| `public_row_id` | Identifier | Release row identifier for deceased records. Missing for living records. | String | 0 | 367 |
| `record_id` | Identifier | Composite identifier for living records. Missing for deceased records. | String | 6795 | 0 |
| `riv_dist` | Spatial provenance | Supplied distance to the nearest classified river segment. | Meters, -999 = no segment within search radius | 6795 | 367 |
| `riv_type` | Hydrology provenance | River-position classification at the maximum search scale. Scale-specific river_type fields enter the models. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_10km` | Hydrology | River-position class at the 10-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_15km` | Hydrology | River-position class at the 15-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_1km` | Hydrology | River-position class at the 1-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_2km` | Hydrology | River-position class at the 2-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_3km` | Hydrology | River-position class at the 3-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `river_type_5km` | Hydrology | River-position class at the 5-km proximity threshold. | 0 = isolated, 1 = upstream, 2 = midstream, 3 = downstream | 6795 | 367 |
| `roof_material` | Control | Roof-material source category used to construct housing PCA. | DHS categorical code | 6795 | 367 |
| `sample_weight` | Weight | Individual sampling weight associated with the interviewed mother and assigned to the child record. Used as sample_weight / 1,000,000. | Positive integer | 6795 | 367 |
| `season` | Time provenance | Prepared interview season label. | Wet or Dry | 6795 | 367 |
| `survey_type` | Survey provenance | Survey source, completed from interview year for deceased records. | DHS = 2018, MIS = 2021 | 6795 | 367 |
| `toilet_type` | Control | Toilet category, entered categorically. | DHS categorical code | 6795 | 367 |
| `wall_material` | Control | Wall-material source category used to construct housing PCA. | DHS categorical code | 6795 | 367 |
| `water_class_label` | Control label | Study-specific label corresponding to water_improved. | Protected_or_delivered, Unprotected, Unclassified | 6795 | 367 |
| `water_improved` | Control | Study-specific binary water-source feature. Source type is a proxy for protection and delivery, not a measured water-quality value. | 1 = codes 11,12,13,31,41,61,62,71; 0 = 32,42; other codes missing | 1135 | 53 |
| `water_source_code` | Control provenance | Reported drinking-water source code, coalesced across living and deceased exports. | DHS categorical code | 6795 | 367 |
| `waz_score` | Other outcome | Prepared weight-for-age z-score. | Z-score | 2052 | 0 |
| `wealth_index` | Control | Household wealth quintile, entered categorically when included. | 1 = poorest through 5 = richest | 6795 | 367 |
| `whz_score` | Other outcome | Prepared weight-for-height z-score. | Z-score | 2046 | 0 |
| `year` | Time provenance | Year of the survey and concurrent OLC assignment. Equals interview_year in this release. | 2018 or 2021 | 6795 | 367 |
