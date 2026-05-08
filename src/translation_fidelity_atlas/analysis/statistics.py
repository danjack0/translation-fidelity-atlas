"""
Inferential statistics on the back-translation dataset.

Functions here are deliberately small: each computes one summary, returns a
DataFrame, and lets the caller print, save, or plot. The CLI wraps them all
into the ``analyse`` script.
"""

from __future__ import annotations

import pandas as pd
from scipy import stats


# --------------------------------------------------------------------------- #
# Summary tables                                                              #
# --------------------------------------------------------------------------- #

def summary_by(df: pd.DataFrame, group: str, metric: str) -> pd.DataFrame:
    """
    Mean, std, and n for ``metric`` grouped by ``group`` (e.g. ``family``).

    Sorted by mean descending for higher-better metrics (cosine, BLEU,
    embedding) and ascending for TER. The sort direction is inferred from the
    metric name.
    """
    higher_better = metric != "ter"
    out = (
        df.groupby(group)[metric]
        .agg(mean="mean", std="std", n="count")
        .round(4)
        .sort_values("mean", ascending=not higher_better)
    )
    return out


# --------------------------------------------------------------------------- #
# ANOVA                                                                       #
# --------------------------------------------------------------------------- #

def one_way_anova(df: pd.DataFrame, factor: str, metric: str) -> dict:
    """
    One-way ANOVA: does ``metric`` differ across levels of ``factor``?

    Returns ``{F, p, df_between, df_within, eta_squared}``. ``eta_squared`` is
    the proportion of total variance attributable to the factor.
    """
    groups = [g[metric].dropna().values for _, g in df.groupby(factor)]
    F, p = stats.f_oneway(*groups)

    grand_mean = df[metric].mean()
    ss_total = ((df[metric] - grand_mean) ** 2).sum()
    means = df.groupby(factor)[metric].mean()
    ns = df.groupby(factor)[metric].count()
    ss_between = (ns * (means - grand_mean) ** 2).sum()
    eta2 = ss_between / ss_total if ss_total else float("nan")

    return {
        "F": float(F),
        "p": float(p),
        "df_between": len(groups) - 1,
        "df_within": int(ns.sum() - len(groups)),
        "eta_squared": float(eta2),
    }


def variance_decomposition(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    η²-style variance decomposition for ``metric`` against ``family``,
    ``domain``, and ``family × domain`` interaction (additive only).
    """
    grand_mean = df[metric].mean()
    ss_total = ((df[metric] - grand_mean) ** 2).sum()

    rows = []
    for factor in ("family", "domain"):
        means = df.groupby(factor)[metric].mean()
        ns = df.groupby(factor)[metric].count()
        ss = (ns * (means - grand_mean) ** 2).sum()
        rows.append({
            "factor": factor,
            "ss": round(ss, 3),
            "eta_squared": round(ss / ss_total, 4) if ss_total else float("nan"),
        })
    rows.append({
        "factor": "total",
        "ss": round(ss_total, 3),
        "eta_squared": 1.0,
    })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Best / worst cells                                                          #
# --------------------------------------------------------------------------- #

def extreme_cells(df: pd.DataFrame, metric: str, n: int = 5) -> dict[str, pd.DataFrame]:
    """Return top-n and bottom-n (language × domain) rows on ``metric``."""
    higher_better = metric != "ter"
    cols = ["family", "language", "domain", metric]
    if higher_better:
        return {
            "best":  df.nlargest(n, metric)[cols].reset_index(drop=True),
            "worst": df.nsmallest(n, metric)[cols].reset_index(drop=True),
        }
    return {
        "best":  df.nsmallest(n, metric)[cols].reset_index(drop=True),
        "worst": df.nlargest(n, metric)[cols].reset_index(drop=True),
    }
