# Figures

All figures are auto-generated from
[`data/results/google/back_translation_long.csv`](../data/results/google/back_translation_long.csv)
by `python scripts/make_figures.py`. Every plot in this directory can be
deleted and recreated; they are committed for portfolio convenience but
are not the source of truth.

## Heatmaps — `heatmap_{translator}_{family}.png`

One per (translator × family). Each is a 1×4 panel: cosine similarity, BLEU,
TER, and embedding similarity, with languages on the y-axis and domains on
the x-axis. Useful for reading off any specific (language, domain) cell.

* `heatmap_google_germanic.png`
* `heatmap_google_romance.png`
* `heatmap_google_slavic.png`
* `heatmap_google_semitic.png`
* `heatmap_google_east_asian.png`
* `heatmap_google_south_se_asian.png`
* `heatmap_google_turkic.png`
* `heatmap_google_uralic.png`

## Family bar charts — `bar_family_{metric}_{translator}.png`

For each metric (cosine, BLEU, TER), a per-family bar chart with grouped
bars by domain. Error bars are ±1 SD across languages within the family.

* `bar_family_cosine_google.png`
* `bar_family_bleu_google.png`  ← *the figure to lead with*
* `bar_family_ter_google.png`

## Domain bar charts — `bar_domain_{metric}.png`

Per-metric bar chart with one bar per domain, optionally grouped by
translator (currently only Google; the second translator will appear once
NLLB is run).

* `bar_domain_cosine.png`
* `bar_domain_bleu.png`
* `bar_domain_ter.png`

## Cross-metric scatter plots — `scatter_{metric_a}_vs_{metric_b}.png`

Each point is one (language, domain) cell. Colour codes family. The OLS line
and Pearson r are overlaid.

* `scatter_cosine_vs_bleu.png` — *the form-vs-meaning correlation*
* `scatter_cosine_vs_ter.png`
* `scatter_bleu_vs_ter.png` — near-perfect anti-correlation

## Box plots — `boxplot_{metric}_{translator}.png`

Per-family distributional spread across all (language × domain) cells. Box
shows IQR; notch shows median CI; whiskers extend to 1.5 × IQR.

* `boxplot_cosine_google.png`
* `boxplot_bleu_google.png`
* `boxplot_ter_google.png`

## Radar charts — `radar_{translator}.png`

One per translator. Three axes (cosine, BLEU normalised to 0–1, 1 − TER/100)
and one polygon per family. Lets you see at a glance which families are
strong on form vs meaning.

* `radar_google.png`

## Correlation matrices — `corr_matrix_{translator}.png`

3×3 Pearson correlation heatmap across (cosine, BLEU, TER) for one
translator, with significance stars.

* `corr_matrix_google.png`

## Telephone-chain plots *(forthcoming)*

Generated when `data/results/google/telephone_chain.csv` exists.

* `chain_degradation_cosine.png`
* `chain_degradation_bleu.png`
* `chain_degradation_ter.png`

Each is a translator × domain grid, with one line per chain order.

## Round-trip plots *(forthcoming)*

Generated when `data/results/google/round_trip.csv` exists.

* `roundtrip_google.png` — per-language ABA vs BAB bars on each metric.
* `asymmetry_heatmap.png` — `|ABA cosine − BAB cosine|` per language.
