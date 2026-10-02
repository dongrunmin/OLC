# Substantial health toll of oil-induced land contamination: Evidence from satellite observations and causal inference

## Description

This dataset contains the core public data products used to analyze oil-contaminated land (OLC), officially reported oil spills, and child-health exposure pathways in the Niger Delta, Nigeria. The dataset includes annual satellite-derived OLC polygon maps for 2016-2023, a cleaned record-level table of official oil-spill reports for 2016-2024, and DHS-derived model-ready health tables used for the child morbidity, infant mortality, and hemoglobin analyses.

The OLC maps were produced from high-resolution satellite image time series using a deep-learning-based mapping workflow. The annual polygon shapefiles represent land areas classified as oil-contaminated in each year. These maps are intended for spatial statistics, state-level summaries, environmental exposure assessment, and comparison with official spill records. The official oil-spill table compiles reported incidents, harmonizes dates and locations, cleans estimated spill quantity and spill-area fields, and assigns records to administrative units when possible. The health tables link DHS child and household records to OLC exposure metrics, river-position classes, and spatial fixed-effect identifiers for regression analysis.


## Data Collection and Processing Summary

### Satellite-derived OLC maps

Annual OLC maps were generated for 2016-2023 from satellite imagery and exported as polygon shapefiles in WGS84 geographic coordinates (`EPSG:4326`). Each shapefile contains polygons for one annual OLC map and a minimal attribute table. The polygons can be reprojected to an equal-area CRS before computing area statistics.

The annual OLC layers included here are:

| Year | Shapefile | Number of polygon features | CRS | Main fields |
|---|---|---:|---|---|
| 2016 | `OLC_maps/2016.shp` | 3,972 | EPSG:4326 | `value`, `geometry` |
| 2017 | `OLC_maps/2017.shp` | 4,400 | EPSG:4326 | `value`, `geometry` |
| 2018 | `OLC_maps/2018.shp` | 4,387 | EPSG:4326 | `value`, `geometry` |
| 2019 | `OLC_maps/2019.shp` | 4,913 | EPSG:4326 | `value`, `geometry` |
| 2020 | `OLC_maps/2020.shp` | 5,583 | EPSG:4326 | `value`, `geometry` |
| 2021 | `OLC_maps/2021.shp` | 6,538 | EPSG:4326 | `value`, `geometry` |
| 2022 | `OLC_maps/2022.shp` | 7,051 | EPSG:4326 | `value`, `geometry` |
| 2023 | `OLC_maps/2023.shp` | 6,547 | EPSG:4326 | `value`, `geometry` |

Each shapefile is distributed with the required companion files: `.shp`, `.shx`, `.dbf`, `.prj`, and `.cpg`. Keep these files together when opening the layers in GIS software.

### Official oil-spill records

`all_official_oil_spill_records_2016-2024.csv` contains 3,509 record-level official oil-spill reports for 2016-2024. The table preserves selected source attributes and adds cleaned analysis fields. Spill quantities are reported in barrels where available, and spill areas are standardized to square kilometers and hectares where the raw text could be parsed reliably.

Key fields include:

| Field | Description |
|---|---|
| `ID` | Unique record identifier in this release. |
| `source_layer` | Source layer or file from which the record was extracted. |
| `Incident d` | Original incident-date field from the source data. |
| `incident_year` | Parsed incident year used for annual summaries. |
| `Latitude`, `Longitude` | Original latitude and longitude fields. |
| `lon`, `lat` | Cleaned longitude and latitude in decimal degrees. |
| `valid_lonlat` | Indicator for whether the cleaned coordinates pass basic validity checks. |
| `ADM1_EN`, `ADM1_PCODE` | Administrative level-1 state name and code assigned to the record. |
| `state_method` | Method used to assign the state, such as spatial join or fallback parsing. |
| `state_weight` | Weight used when a record is allocated across multiple states. |
| `record_count_weighted` | Weighted record count used in state-level summaries. |
| `Estimated` | Original estimated spill-quantity field. |
| `estimated_bbl` | Cleaned estimated spill quantity in barrels. |
| `Spill area` | Original spill-area text field. |
| `area_numeric_raw` | Numeric value parsed from the original spill-area text, before unit harmonization. |
| `spill_area_km2` | Cleaned spill area in square kilometers. Missing when the raw area could not be parsed reliably. |
| `spill_area_ha` | Cleaned spill area in hectares. |
| `area_cleaning_rule` | Rule used to parse, convert, or reject the raw spill-area text. |
| `Cause`, `Type of fa`, `Company`, `LGA`, `Status` | Selected source attributes describing the reported incident. |

### DHS-derived health data

`Health_data/all_living_and_deceased_model_ready.csv` is the single combined input for the health analyses. It contains **7,162 records and 82 columns**, including 6,795 surviving children and 367 deceased children. Records are linked to the 2018 Nigeria DHS or the 2021 Nigeria Malaria Indicator Survey (MIS), satellite-derived OLC areas, river-position classes, and spatial grid identifiers. See `HEALTH_DATA_DICTIONARY.md` for all fields and their observed availability.

| Survey | Surviving records | Deceased records | Total |
|---|---:|---:|---:|
| 2018 DHS | 4,782 | 322 | 5,104 |
| 2021 MIS | 2,013 | 45 | 2,058 |
| Total | 6,795 | 367 | 7,162 |

For the code repository, place the same file in `data/health/`. The scripts in `Health_script/` construct each outcome-specific sample directly from this combined table. A separate infant-mortality risk-set CSV is no longer required.

| Analysis | Sample rule | Exposure | River-proximity scales |
|---|---|---|---|
| Complete-case diarrhea | Surviving children interviewed in 2018 with observed diarrhea and all included controls, including classifiable water-source status | `log1p` of current-year OLC area within 10 or 15 km | 1, 2, 3, 5, 10, 15 km |
| Expanded diarrhea | Same rule, omitting only the water-source control and retaining wealth | Same current-year exposures | 1, 2, 3, 5, 10, 15 km |
| Recent-birth mortality | Both surviving and deceased records with `0 <= child_age_months < 12`, pooled across 2018 and 2021, without water-source or wealth controls | `log1p` of prior-three-year mean OLC area within 15 km | 3, 5, 10, 15 km |
| Survivor-only Hb | Surviving children with observed Hb and complete included controls, including water source and wealth | Same prior-three-year exposure | 3, 5, 10, 15 km |
| Mortality-inclusive Hb sensitivity | Observed survivor Hb plus deceased records assigned Hb = 0 within the model, with the same controls | Same prior-three-year exposure | 3, 5, 10, 15 km |

The diarrhea samples contain 619 and 4,765 observations, respectively, at every evaluated river-proximity scale. The mortality candidate cohort contains 1,367 records before the river restriction. For deceased children, `child_age_months` is the elapsed time from birth to interview. All 367 deceased records agree with the month interval calculated from the supplied birth and interview dates. This recent-birth criterion includes the 2021 deaths despite unavailable age-at-death information and excludes earlier birth cohorts. The CSV does not contain `b7`, death dates, or a separate verified age-at-death variable. The mortality analysis estimates recorded death among recent births, rather than a life-table infant mortality rate.

| River scale | Mortality N | Deaths | Survivor-only Hb N | Mortality-inclusive Hb N | Included Hb deaths |
|---|---:|---:|---:|---:|---:|
| 3 km | 224 | 5 | 160 | 167 | 7 |
| 5 km | 325 | 10 | 206 | 213 | 7 |
| 10 km | 478 | 18 | 322 | 333 | 11 |
| 15 km | 568 | 24 | 358 | 373 | 15 |

River classes are `0 = isolated`, `1 = upstream`, `2 = midstream`, and `3 = downstream`. Diarrhea models combine upstream and isolated records as the comparison group. Mortality and Hb models exclude isolated records and compare upstream with combined midstream/downstream records.

OLC areas are in km². Current-year fields are `olc_area_km2_{5,10,15}km`. Prior-three-year mean fields are `olc_mean_area_km2_{5,10,15}km`. Their corresponding `log_olc_*` fields equal `ln(1 + area)`. OLC aggregation radius and river-proximity scale are separate settings. The modeling scripts use the supplied spatial features and do not recompute polygon intersections.

The updated CSV preserves all records, row order, source outcomes, weights, and model covariates. Nine redundant aliases were removed after checking agreement. Partial water-source codes were coalesced into `water_source_code`, missing OLC logs were filled from raw areas, survey labels were completed using the interview year, and water-class labels were standardized. No mortality assignment was written into source Hb. `all_living_and_deceased_model_ready.cleaning_report.json` records these changes.

## Missing Values and Special Codes

- Blank CSV cells represent missing values unless otherwise noted.
- `riv_dist = -999` marks DHS clusters with no classified river segment within the maximum search radius.
- `spill_area_km2` is missing when the original official spill-area text was absent, ambiguous, or could not be converted reliably.
- `estimated_bbl = 0` may indicate a reported zero quantity or a record for which the cleaned estimate was set to zero under the documented cleaning rule. Users should inspect source fields such as `Estimated` and `Quantity r` for specialized spill-volume analyses.
- DHS displaced coordinates (`LATNUM`, `LONGNUM`) are cluster-level coordinates and should not be used as exact household locations.

