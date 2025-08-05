from __future__ import annotations

from typing import Any

import pandas as pd

SCORE_WEIGHTS = {
    "posting_frequency": 0.25,
    "avg_views": 0.30,
    "top_post_views": 0.15,
    "avg_price": 0.20,
    "price_coverage": 0.10,
}


def _minmax(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return 100.0 * (series - lo) / (hi - lo)


def _parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce")


def build_vendor_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["date"] = _parse_dates(work["date"])
    work["views"] = pd.to_numeric(work["views"], errors="coerce").fillna(0)
    work["prices"] = work["prices"].apply(lambda x: x if isinstance(x, list) else [])
    work["n_prices"] = work["prices"].apply(len)
    work["mean_price"] = work["prices"].apply(
        lambda xs: float(sum(xs) / len(xs)) if xs else float("nan")
    )

    rows: list[dict[str, Any]] = []
    for channel, g in work.groupby("channel", dropna=False):
        dates = g["date"].dropna()
        span_days = 1.0
        if len(dates) >= 2:
            span_days = max((dates.max() - dates.min()).total_seconds() / 86400.0, 1.0)
        posts = len(g)
        posts_per_week = posts / span_days * 7.0
        avg_views = float(g["views"].mean())
        top_idx = g["views"].idxmax()
        top_row = g.loc[top_idx]
        priced = g[g["n_prices"] > 0]
        avg_price = float(priced["mean_price"].mean()) if len(priced) else float("nan")
        price_coverage = float((g["n_prices"] > 0).mean())

        rows.append(
            {
                "vendor": channel,
                "n_posts": posts,
                "span_days": round(span_days, 2),
                "posting_frequency_per_week": round(posts_per_week, 3),
                "avg_views": round(avg_views, 2),
                "top_post_message_id": int(top_row["message_id"])
                if pd.notna(top_row["message_id"])
                else None,
                "top_post_views": int(top_row["views"]),
                "top_post_preview": str(top_row.get("cleaned_text") or "")[:160],
                "avg_price_etb": round(avg_price, 2) if pd.notna(avg_price) else None,
                "price_coverage": round(price_coverage, 3),
                "n_posts_with_price": int((g["n_prices"] > 0).sum()),
            }
        )

    scorecard = pd.DataFrame(rows)
    if scorecard.empty:
        return scorecard

    norm_freq = _minmax(scorecard["posting_frequency_per_week"])
    norm_views = _minmax(scorecard["avg_views"])
    norm_top = _minmax(scorecard["top_post_views"])
    price_for_norm = scorecard["avg_price_etb"].fillna(scorecard["avg_price_etb"].median())
    if price_for_norm.isna().all():
        price_for_norm = pd.Series([0.0] * len(scorecard), index=scorecard.index)
    norm_price = _minmax(price_for_norm)
    norm_cov = _minmax(scorecard["price_coverage"])

    scorecard["lending_score"] = (
        SCORE_WEIGHTS["posting_frequency"] * norm_freq
        + SCORE_WEIGHTS["avg_views"] * norm_views
        + SCORE_WEIGHTS["top_post_views"] * norm_top
        + SCORE_WEIGHTS["avg_price"] * norm_price
        + SCORE_WEIGHTS["price_coverage"] * norm_cov
    ).round(2)

    scorecard = scorecard.sort_values("lending_score", ascending=False).reset_index(drop=True)
    scorecard.insert(0, "rank", range(1, len(scorecard) + 1))
    return scorecard
