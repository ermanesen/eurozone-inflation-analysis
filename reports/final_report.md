# Eurozone Inflation and Unemployment: Correcting and Re-estimating the Panel Evidence

## Executive summary

This project estimates the relationship between annual HICP inflation and lagged unemployment across eight euro-area economies from January 2000 to December 2025. It corrects two measurement problems in the original implementation: an annual HICP inflation rate was mistakenly transformed again with a 12-month percentage change, and multiple unemployment seasonal-adjustment variants were merged as duplicate country-month records.

The corrected data contain 2,496 unique and complete country-month observations. After constructing a six-month within-country unemployment lag, 2,448 observations enter the regressions. The unemployment coefficient is -0.259 (clustered SE 0.055, p=0.002) with country fixed effects and -0.106 (clustered SE 0.013, p<0.001) with both country and month fixed effects. Common monthly shocks attenuate the relationship but do not reverse it.

## Measurement correction

Eurostat `prc_hicp_manr` with unit `RCH_A` is already the annual rate of change in the all-items HICP. Its values are percentage-point annual inflation rates. Applying `pct_change(12) * 100` would instead calculate the percentage change of an inflation rate—an unstable quantity with no standard Phillips-curve interpretation. The corrected dependent variable is therefore the published `hicp_annual_rate` itself.

For unemployment, the pipeline now requests `une_rt_m` with `s_adj=SA`, `age=TOTAL`, `sex=T`, and `unit=PC_ACT`. Country-month uniqueness is asserted before merging. The analysis no longer permits several adjustment variants to produce repeated observations.

## Data audit

The configured panel is a full Cartesian product of eight countries and 312 months. All 2,496 expected keys have both HICP and unemployment data in the committed snapshot. The exact six-month lag removes the first six observations in each country, producing 2,448 model rows. The pipeline records expected rows, complete rows, missingness, duplicate keys, and lag attrition in `reports/tables/quality_summary.json`.

## Descriptive evidence

Average annual HICP inflation across the sample peaked at 11.34% in October 2022. The pooled average was 1.46% during 2010–2019, increased to 5.46% during 2021–2023, and fell to 2.41% in 2025. This path makes common time shocks central to the model design.

## Econometric design and results

The first model includes country fixed effects. Its coefficient of -0.259 means that one percentage point higher unemployment six months earlier is associated with 0.259 percentage points lower annual HICP inflation within a country.

The second model adds calendar-month fixed effects. These absorb any shock shared by all sample countries in a given month. The coefficient shrinks to -0.106. The reduction is substantively important: common shocks explain part of the raw within-country relationship. Contrary to the original claim, however, the corrected relationship remains negative rather than reversing sign.

Standard errors are clustered by country because observations from the same economy are serially related. The sample has only eight clusters, so conventional cluster-robust inference can be optimistic. Results should be read primarily through effect size and model sensitivity.

## Limitations

- This is not a causal design; unemployment is not randomly assigned and the lag does not create exogeneity.
- Eight country clusters limit precision and motivate small-cluster corrections in future work.
- Eurostat revises both HICP and unemployment data, so refreshed snapshots may change estimates.
- A common slope masks heterogeneous Phillips curves across countries and policy regimes.
- Supply shocks, inflation expectations, wages, fiscal policy, and energy exposure are not modeled directly.
- The sample is a focused eight-country panel rather than every euro-area member.

## Next steps

A stronger extension would add energy-price exposure and inflation expectations, estimate country- or period-varying slopes, use wild-cluster bootstrap inference, test alternative lags, and separate pre-pandemic, pandemic, and energy-shock regimes. Those additions would deepen the analysis without overstating what the current fixed-effects specifications identify.
