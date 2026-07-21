import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from models.core import (
    build_regression_forecast,
    predict_prophet_for_quarters,
)
from services.news_fetcher import (
    NewsAPIError,
    fetch_external_news,
    score_market_articles,
)
from ui.navigation import go_to_page


CACHE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "market_intelligence_cache.json"
)
MAX_CACHE_ENTRIES = 50


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_cached_external_news():
    return fetch_external_news(page_size=30, keep_top=5)


def _market_adjustment_percent(market_score: float) -> float:
    """
    Convert a Market Impact Score from -100 to +100 into a small,
    transparent revenue adjustment from -3% to +3%.

    Examples:
        +100 -> +3.0%
         +50 -> +1.5%
           0 ->  0.0%
         -50 -> -1.5%
        -100 -> -3.0%
    """
    bounded_score = max(-100.0, min(100.0, float(market_score)))
    return round(bounded_score * 0.03, 4)

def _market_adjustment_decay(
    horizon_quarters: int,
    decay_rate: float = 0.70,
) -> float:
    """
    Reduce the influence of current news for forecasts further into the future.

    1 quarter ahead -> 100%
    2 quarters ahead -> 70%
    3 quarters ahead -> 49%
    4 quarters ahead -> 34.3%
    """
    horizon = max(1, int(horizon_quarters))
    return decay_rate ** (horizon - 1)


def _find_revenue_column(forecast_df):
    """
    Find the most likely forecast revenue column without depending on
    one exact model-output column name.
    """
    preferred_names = [
        "Predicted Revenue",
        "Forecast Revenue",
        "Revenue Forecast",
        "Revenue",
        "yhat",
    ]

    for name in preferred_names:
        if name in forecast_df.columns:
            return name

    for column in forecast_df.columns:
        lowered = str(column).lower()
        if "revenue" in lowered and (
            "predict" in lowered
            or "forecast" in lowered
            or lowered == "revenue"
        ):
            return column

    return None


def _apply_market_adjustment(
    forecast_df,
    latest_quarter_no: int,
):
    """
    Apply Gemini's market adjustment with time decay.

    Current news receives full weight for the next quarter and gradually
    becomes less important for forecasts further into the future.
    """
    market_result = st.session_state.get("market_intelligence_score")

    if not market_result:
        return forecast_df, {
            "market_score": 0.0,
            "base_adjustment_percent": 0.0,
            "adjustment_percent": 0.0,
            "decay_factor": 0.0,
            "horizon_quarters": 0,
            "applied": False,
            "reason": "Market intelligence was unavailable.",
        }

    market_score = float(
        market_result.get("market_score", 0.0)
    )

    base_adjustment_percent = _market_adjustment_percent(
        market_score
    )

    revenue_column = _find_revenue_column(forecast_df)

    if revenue_column is None:
        return forecast_df, {
            "market_score": market_score,
            "base_adjustment_percent": base_adjustment_percent,
            "adjustment_percent": 0.0,
            "decay_factor": 0.0,
            "horizon_quarters": 0,
            "applied": False,
            "reason": "No forecast revenue column was found.",
        }

    adjusted_df = forecast_df.copy()

    base_column = "Base Model Revenue"
    adjusted_column = "Market Adjusted Revenue"
    weight_column = "Market News Weight"
    percent_column = "Effective Market Adjustment (%)"

    adjusted_df[base_column] = adjusted_df[revenue_column]

    effective_adjustments = []
    decay_factors = []
    horizons = []

    for row_index, row in adjusted_df.iterrows():
        if "Quarter No" in adjusted_df.columns:
            forecast_quarter_no = int(row["Quarter No"])
            horizon_quarters = max(
                1,
                forecast_quarter_no - latest_quarter_no,
            )
        else:
            horizon_quarters = row_index + 1

        decay_factor = _market_adjustment_decay(
            horizon_quarters
        )

        effective_adjustment = (
            base_adjustment_percent * decay_factor
        )

        horizons.append(horizon_quarters)
        decay_factors.append(decay_factor)
        effective_adjustments.append(
            effective_adjustment
        )

    adjusted_df["Forecast Horizon (Quarters)"] = horizons
    adjusted_df[weight_column] = decay_factors
    adjusted_df[percent_column] = effective_adjustments

    adjusted_df[adjusted_column] = (
        adjusted_df[base_column]
        * (
            1
            + adjusted_df[percent_column] / 100
        )
    )

    # Keep the existing forecast revenue column as the final displayed value.
    adjusted_df[revenue_column] = adjusted_df[adjusted_column]

    target_horizon = int(horizons[-1])
    target_decay = float(decay_factors[-1])
    target_adjustment = float(effective_adjustments[-1])

    return adjusted_df, {
        "market_score": market_score,
        "base_adjustment_percent": base_adjustment_percent,
        "adjustment_percent": target_adjustment,
        "decay_factor": target_decay,
        "horizon_quarters": target_horizon,
        "applied": True,
        "revenue_column": revenue_column,
        "base_column": base_column,
        "adjusted_column": adjusted_column,
        "weight_column": weight_column,
        "percent_column": percent_column,
    }


def generate_forecast(df, use_market_intelligence):
    config = st.session_state.get("forecast_config")

    if not config:
        st.error(
            "Forecast settings were not found. Return to Forecast Setup "
            "and click Next again."
        )
        return False

    approach = config["approach"]
    model_name = config["model_name"]
    target_period = config["target_period"]
    target_quarter_no = int(config["target_quarter_no"])
    inflation = float(config["inflation"])
    use_tariff = bool(config["use_tariff"])

    latest_quarter_no = int(df["Quarter No"].max())

    if target_quarter_no <= latest_quarter_no:
        st.error(
            f"Choose a forecast quarter after {df.iloc[-1]['Quarter']}."
        )
        return False

    with st.spinner("Generating forecast..."):
        if approach == "Regression Based":
            forecast_df, _ = build_regression_forecast(
                data=df,
                model_name=model_name,
                target_quarter_no=target_quarter_no,
                inflation=inflation,
                tariff=1 if use_tariff else 0,
            )
        else:
            future_quarters = list(
                range(
                    latest_quarter_no + 1,
                    target_quarter_no + 1,
                )
            )

            forecast_df, _ = predict_prophet_for_quarters(
                train_data=df,
                quarter_numbers=future_quarters,
            )

        market_adjustment = {
            "market_score": 0.0,
            "base_adjustment_percent": 0.0,
            "adjustment_percent": 0.0,
            "decay_factor": 0.0,
            "horizon_quarters": 0,
            "applied": False,
            "reason": "Market intelligence was not selected.",
        }

        if use_market_intelligence:
            forecast_df, market_adjustment = _apply_market_adjustment(
                forecast_df=forecast_df,
                latest_quarter_no=latest_quarter_no,
            )

    st.session_state["forecast_output"] = {
        "forecast_df": forecast_df,
        "approach": approach,
        "model_name": model_name,
        "target_period": target_period,
        "use_market_intelligence": use_market_intelligence,
        "market_intelligence": st.session_state.get(
            "market_intelligence_score"
        ),
        "market_adjustment": market_adjustment,
    }

    return True


def _score_label(score: float) -> str:
    if score >= 60:
        return "Strongly Positive"
    if score >= 20:
        return "Positive"
    if score > -20:
        return "Neutral"
    if score > -60:
        return "Negative"
    return "Strongly Negative"


def _article_impact_label(score: float) -> str:
    if score >= 0.35:
        return "Strong positive impact"
    if score >= 0.10:
        return "Positive impact"
    if score > -0.10:
        return "Neutral impact"
    if score > -0.35:
        return "Negative impact"
    return "Strong negative impact"


def _render_market_score(market_result: dict):
    score = float(market_result.get("market_score", 0.0))
    label = _score_label(score)
    adjustment = _market_adjustment_percent(score)
    confidence = float(market_result.get("confidence", 0.0))
    summary = market_result.get("summary", "")
    opportunities = market_result.get("opportunities", [])
    risks = market_result.get("risks", [])

    score_col, adjustment_col, confidence_col = st.columns(3)

    with score_col:
        st.metric("Market Impact Score", f"{score:+.0f} / 100")
        st.caption(f"Market outlook: {label}")

    with adjustment_col:
        st.metric("Revenue Adjustment", f"{adjustment:+.2f}%")
        st.caption("Applied to the base model forecast.")

    with confidence_col:
        st.metric("AI Confidence", f"{confidence:.0f}%")
        st.caption("Confidence in the retrieved evidence.")

    if summary:
        st.markdown("#### Gemini Analysis")
        st.write(summary)

    opportunity_col, risk_col = st.columns(2)

    with opportunity_col:
        st.markdown("#### Opportunities")
        if opportunities:
            for opportunity in opportunities:
                st.markdown(f"- {opportunity}")
        else:
            st.caption("No major opportunities were identified.")

    with risk_col:
        st.markdown("#### Risks")
        if risks:
            for risk in risks:
                st.markdown(f"- {risk}")
        else:
            st.caption("No major risks were identified.")


def _render_articles(articles: list[dict]):
    article_count = len(articles)

    with st.expander(
        f"View selected articles ({article_count})",
        expanded=False,
    ):
        for index, article in enumerate(articles):
            title = article.get("title") or "Untitled article"
            source = article.get("source") or "Unknown source"
            published_at = article.get("published_at") or "Date unavailable"
            impact_score = float(article.get("impact_score", 0.0))

            st.markdown(f"**{title}**")
            st.caption(f"{source} · {published_at}")
            st.caption(
                f"{_article_impact_label(impact_score)} · "
                f"Article score: {impact_score * 100:+.1f}"
            )

            impact_reason = article.get("impact_reason")
            if impact_reason:
                st.write(impact_reason)

            description = article.get("description")
            if description:
                st.caption(description)

            url = article.get("url")
            if url:
                st.link_button(
                    "Read source",
                    url,
                    key=f"article_link_{index}",
                )

            if index < article_count - 1:
                st.divider()


def _article_fingerprint(company: str, articles: list[dict]) -> str:
    """Create a stable key for a company and its selected article set."""
    article_identity = [
        {
            "url": (article.get("url") or "").strip(),
            "title": (article.get("title") or "").strip(),
            "published_at": article.get("published_at") or "",
        }
        for article in articles
    ]

    payload = json.dumps(
        {
            "company": (company or "").strip().lower(),
            "articles": article_identity,
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_persistent_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}

    try:
        with CACHE_PATH.open("r", encoding="utf-8") as cache_file:
            payload = json.load(cache_file)

        if isinstance(payload, dict):
            return payload
    except (OSError, json.JSONDecodeError):
        pass

    return {}


def _read_cached_market_result(fingerprint: str) -> dict | None:
    cache = _load_persistent_cache()
    entry = cache.get(fingerprint)

    if not isinstance(entry, dict):
        return None

    result = entry.get("result")
    return result if isinstance(result, dict) else None


def _save_cached_market_result(
    fingerprint: str,
    company: str,
    articles: list[dict],
    result: dict,
) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache = _load_persistent_cache()

    cache[fingerprint] = {
        "company": company,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "article_urls": [
            article.get("url")
            for article in articles
            if article.get("url")
        ],
        "result": result,
    }

    if len(cache) > MAX_CACHE_ENTRIES:
        sorted_entries = sorted(
            cache.items(),
            key=lambda item: item[1].get("created_at", ""),
            reverse=True,
        )
        cache = dict(sorted_entries[:MAX_CACHE_ENTRIES])

    temporary_path = CACHE_PATH.with_suffix(".tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file, indent=2, ensure_ascii=False)

        temporary_path.replace(CACHE_PATH)
    except OSError:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass


def render_external_intelligence(df):
    title_col, refresh_col = st.columns([4, 1])

    with title_col:
        st.subheader("AI Market Intelligence")

    with refresh_col:
        st.write("")
        if st.button(
            "↻ Refresh",
            key="refresh_external_news",
            use_container_width=True,
        ):
            get_cached_external_news.clear()
            st.session_state.pop("market_intelligence_score", None)
            st.session_state.pop("market_intelligence_fingerprint", None)
            st.rerun()

    config = st.session_state.get("forecast_config")

    if config:
        st.caption(
            f"Current forecast: {config['model_name']} · "
            f"{config['target_period']}"
        )

    try:
        articles = get_cached_external_news()
        article_count = len(articles)
        company = st.session_state.get(
            "company_selector",
            "Selected company",
        )

        if not articles:
            st.caption(
                "No sufficiently relevant articles were found during "
                "this refresh."
            )
            st.session_state.pop("market_intelligence_score", None)
            st.session_state.pop("market_intelligence_fingerprint", None)
        else:
            st.write(
                f"**{article_count} high-relevance articles** selected from "
                "the last 3 days."
            )

            fingerprint = _article_fingerprint(company, articles)
            saved_fingerprint = st.session_state.get(
                "market_intelligence_fingerprint"
            )
            market_result = st.session_state.get(
                "market_intelligence_score"
            )

            if market_result is None or saved_fingerprint != fingerprint:
                market_result = _read_cached_market_result(fingerprint)

                if market_result is None:
                    with st.spinner(
                        "Gemini is reading and scoring new articles..."
                    ):
                        market_result = score_market_articles(
                            articles=articles,
                            company=company,
                        )

                    if not market_result:
                        raise NewsAPIError(
                            "Gemini did not return a market intelligence result."
                        )

                    _save_cached_market_result(
                        fingerprint=fingerprint,
                        company=company,
                        articles=articles,
                        result=market_result,
                    )

                st.session_state["market_intelligence_score"] = market_result
                st.session_state[
                    "market_intelligence_fingerprint"
                ] = fingerprint

            _render_market_score(market_result)

            scored_articles = market_result.get("articles") or articles
            _render_articles(scored_articles)

    except NewsAPIError as exc:
        st.error(str(exc))
        st.session_state.pop("market_intelligence_score", None)
        st.session_state.pop("market_intelligence_fingerprint", None)
    except Exception as exc:
        st.error(
            "Market intelligence could not be generated. "
            f"Details: {exc}"
        )
        st.session_state.pop("market_intelligence_score", None)
        st.session_state.pop("market_intelligence_fingerprint", None)

    with st.expander("How is the Market Impact Score calculated?"):
        st.markdown(
            """
The app retrieves recent external news and keeps the **5 most relevant
developments from the last 3 days**.

Gemini uses URL Context to read the accessible article pages and scores each
article according to its expected effect on the selected company's
**next-quarter revenue**.

The analysis considers developments affecting:

- Pricing, tariffs and ARPU
- Subscribers and customer demand
- Competition
- Regulation and spectrum
- Network investment and technology
- Inflation and operating conditions

Gemini combines the article-level assessments into a **Market Impact Score
from -100 to +100**.

The score creates a controlled revenue adjustment:

`Revenue adjustment (%) = Market Impact Score × 0.03`

The maximum adjustment is **+3%**, and the minimum adjustment is **-3%**.

`Final forecast = Base forecast × (1 + adjustment / 100)`

The regression or Prophet model remains the base prediction. Gemini only
quantifies the likely effect of current external developments.
"""
        )

    st.divider()

    back_col, _, generate_col = st.columns([1, 2, 1.4])

    with back_col:
        if st.button(
            "← Back",
            use_container_width=True,
            key="intelligence_back_button",
        ):
            go_to_page("setup")
            st.rerun()

    with generate_col:
        if st.button(
            "Generate Forecast →",
            type="primary",
            key="generate_forecast_button",
            use_container_width=True,
        ):
            if st.session_state.get("market_intelligence_score") is None:
                st.error(
                    "Market intelligence is not ready yet. "
                    "Refresh the page and try again."
                )
            elif generate_forecast(
                df=df,
                use_market_intelligence=True,
            ):
                go_to_page("results")
                st.rerun()