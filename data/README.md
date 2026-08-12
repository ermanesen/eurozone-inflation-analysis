# Data

`processed/eurozone_macro_panel.csv` is the versioned analysis snapshot used by the published notebook, figures, tests, and report. It contains the annual HICP rate and a single seasonally adjusted unemployment rate for every configured country-month.

Raw downloads are intentionally ignored. Run `python scripts/run_analysis.py --refresh` to request both Eurostat datasets with the filters in `config/analysis.toml`, validate the full panel, and replace the processed snapshot.

Eurostat sources:

- `prc_hicp_manr`: HICP annual rate of change, all-items `CP00`, unit `RCH_A`.
- `une_rt_m`: monthly unemployment, seasonally adjusted `SA`, total age and sex, percentage of active population `PC_ACT`.
