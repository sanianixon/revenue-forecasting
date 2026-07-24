import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError
import requests
import streamlit as st
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

NEWS_API_URL = "https://newsapi.org/v2/everything"
MODEL_COOLDOWN_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "gemini_model_cooldowns.json"
)

GEMINI_MODELS = [
    ("gemini-3.5-flash-lite", "Gemini 3.5 Flash Lite"),
    ("gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite"),
    ("gemini-3.5-flash", "Gemini 3.5 Flash"),
]


POSITIVE_TERMS = {
    "accelerate", "approval", "boost", "expansion", "gain", "growth",
    "improve", "increase", "investment", "launch", "partnership",
    "profit", "record", "recovery", "rise", "strong", "surge", "upgrade",
}

NEGATIVE_TERMS = {
    "ban", "conflict", "decline", "delay", "disruption", "drop", "fall",
    "fine", "inflation", "loss", "penalty", "pressure", "risk",
    "sanction", "slowdown", "strike", "war", "weak",
}

TELECOM_TERMS = {
    "airtel", "bharti airtel", "jio", "reliance jio",
    "vodafone idea", "telecom", "trai", "spectrum", "5g",
    "subscriber", "subscribers", "arpu", "tariff", "broadband",
    "mobile network", "network rollout", "data customer",
}

ECONOMIC_TERMS = {
    "inflation", "gdp", "economy", "economic growth", "repo rate",
    "interest rate", "rupee", "oil price", "consumer spending",
    "rbi", "monetary policy",
}

GEOPOLITICAL_TERMS = {
    "war", "conflict", "sanction", "sanctions", "geopolitical",
    "trade restriction", "border tension", "supply disruption",
}

HIGH_IMPORTANCE_TERMS = {
    "tariff", "spectrum", "regulation", "trai", "merger",
    "acquisition", "ban", "sanction", "sanctions", "war",
    "repo rate", "interest rate", "license", "fine", "penalty",
}

MEDIUM_IMPORTANCE_TERMS = {
    "5g", "subscriber", "subscribers", "arpu", "investment",
    "launch", "expansion", "partnership", "inflation", "gdp",
    "oil price", "network", "rupee",
}

# This list only removes obviously unrelated content.
# It does not require every article to be telecom-specific.
IRRELEVANT_TERMS = {
    "box office", "movie review", "film review", "cinema",
    "actor", "actress", "bollywood", "hollywood", "trailer",
    "ott release", "cricket score", "football match", "tennis match",
    "celebrity", "music album", "web series", "recipe",
    "horoscope", "fashion show", "wedding photos",
}


def get_news_api_key():
    try:
        return st.secrets["NEWS_API_KEY"]
    except Exception:
        return os.getenv("NEWS_API_KEY")
    
def get_gemini_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")


class NewsAPIError(Exception):
    """Raised when news collection fails."""


def _load_model_cooldowns() -> dict:
    if not MODEL_COOLDOWN_PATH.exists():
        return {}

    try:
        with MODEL_COOLDOWN_PATH.open("r", encoding="utf-8") as cooldown_file:
            payload = json.load(cooldown_file)
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_model_cooldowns(cooldowns: dict) -> None:
    MODEL_COOLDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = MODEL_COOLDOWN_PATH.with_suffix(".tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as cooldown_file:
            json.dump(cooldowns, cooldown_file, indent=2)
        temporary_path.replace(MODEL_COOLDOWN_PATH)
    except OSError:
        temporary_path.unlink(missing_ok=True)


def _active_model_cooldown(model_id: str) -> datetime | None:
    cooldowns = _load_model_cooldowns()
    blocked_until_text = cooldowns.get(model_id)

    if not blocked_until_text:
        return None

    try:
        blocked_until = datetime.fromisoformat(blocked_until_text)
    except (TypeError, ValueError):
        cooldowns.pop(model_id, None)
        _save_model_cooldowns(cooldowns)
        return None

    if blocked_until <= datetime.now(timezone.utc):
        cooldowns.pop(model_id, None)
        _save_model_cooldowns(cooldowns)
        return None

    return blocked_until


def _next_pacific_midnight_utc() -> datetime:
    pacific = ZoneInfo("America/Los_Angeles")
    now_pacific = datetime.now(pacific)
    tomorrow = now_pacific.date() + timedelta(days=1)
    reset_pacific = datetime.combine(
        tomorrow,
        datetime.min.time(),
        tzinfo=pacific,
    )
    return reset_pacific.astimezone(timezone.utc)


def _is_quota_error(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return (
        getattr(exc, "code", None) == 429
        or "429" in error_text
        or "resource_exhausted" in error_text
    )


def _quota_cooldown_until(exc: Exception) -> datetime:
    error_text = str(exc).lower()
    daily_markers = (
        "perday",
        "per_day",
        "per day",
        "requestsperday",
        "rpd",
        "daily",
    )

    if any(marker in error_text for marker in daily_markers):
        return _next_pacific_midnight_utc()

    retry_match = re.search(
        r"retry(?:\s+in|\s+after)?\s*([0-9]+(?:\.[0-9]+)?)\s*s",
        error_text,
    )
    retry_seconds = (
        max(60, int(float(retry_match.group(1))) + 5)
        if retry_match
        else 60
    )
    return datetime.now(timezone.utc) + timedelta(seconds=retry_seconds)


def _block_model_after_quota_error(
    model_id: str,
    exc: Exception,
) -> datetime:
    blocked_until = _quota_cooldown_until(exc)
    cooldowns = _load_model_cooldowns()
    cooldowns[model_id] = blocked_until.isoformat()
    _save_model_cooldowns(cooldowns)
    return blocked_until


def _normalise_text(article: dict) -> str:
    return " ".join(
        [
            article.get("title") or "",
            article.get("description") or "",
        ]
    ).lower()


def _contains_term(text: str, term: str) -> bool:
    return bool(
        re.search(
            rf"\b{re.escape(term.lower())}\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(_contains_term(text, term) for term in terms)


def _count_terms(text: str, terms: set[str]) -> int:
    return sum(_contains_term(text, term) for term in terms)


def _is_obviously_irrelevant(text: str) -> bool:
    return _contains_any(text, IRRELEVANT_TERMS)


def _retrieval_relevance_score(
    text: str,
    company: str = "",
) -> float:
    """
    Rank rather than hard-filter.

    Telecom articles rank highest, but broader economic and geopolitical
    developments remain eligible because they can still affect revenue.
    """
    score = 0.0

    company_name = str(company).strip().casefold()
    normalised_text = str(text).casefold()

    # Strongly prioritise articles that directly name the selected company.
    if company_name and company_name in normalised_text:
        score += 12.0

    telecom_matches = _count_terms(text, TELECOM_TERMS)
    economic_matches = _count_terms(text, ECONOMIC_TERMS)
    geopolitical_matches = _count_terms(text, GEOPOLITICAL_TERMS)

    score += min(telecom_matches * 2.0, 10.0)
    score += min(economic_matches * 1.0, 4.0)
    score += min(geopolitical_matches * 0.8, 3.2)

    if _contains_any(text, HIGH_IMPORTANCE_TERMS):
        score += 2.0
    elif _contains_any(text, MEDIUM_IMPORTANCE_TERMS):
        score += 1.0

    return score


def _deduplicate_articles(articles: list[dict]) -> list[dict]:
    unique_articles = []
    seen_urls = set()
    seen_titles = set()

    for article in articles:
        url = (article.get("url") or "").strip().lower()
        title_key = re.sub(
            r"[^a-z0-9]+",
            " ",
            (article.get("title") or "").lower(),
        ).strip()

        if url and url in seen_urls:
            continue

        if title_key and title_key in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title_key:
            seen_titles.add(title_key)

        unique_articles.append(article)

    return unique_articles


def _score_sentiment(text: str) -> float:
    positive_count = _count_terms(text, POSITIVE_TERMS)
    negative_count = _count_terms(text, NEGATIVE_TERMS)

    if positive_count == 0 and negative_count == 0:
        return 0.0

    score = (
        positive_count - negative_count
    ) / max(positive_count + negative_count, 1)

    return max(-1.0, min(1.0, score))


def _score_relevance(text: str, company: str) -> float:
    company_name = (company or "").strip().lower()

    if (
        company_name
        and company_name not in {"custom company", "selected company"}
        and _contains_term(text, company_name)
    ):
        return 1.0

    if _contains_any(text, TELECOM_TERMS):
        return 0.85

    if _contains_any(text, ECONOMIC_TERMS):
        return 0.60

    if _contains_any(text, GEOPOLITICAL_TERMS):
        return 0.45

    return 0.25


def _score_importance(text: str) -> float:
    if _contains_any(text, HIGH_IMPORTANCE_TERMS):
        return 1.0

    if _contains_any(text, MEDIUM_IMPORTANCE_TERMS):
        return 0.75

    return 0.45


def _parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _score_recency(published_at: str | None) -> float:
    published = _parse_published_at(published_at)

    if published is None:
        return 0.50

    age_days = max(
        0,
        (datetime.now(timezone.utc) - published).days,
    )

    if age_days <= 1:
        return 1.00
    if age_days <= 2:
        return 0.90
    if age_days <= 3:
        return 0.80
    if age_days <= 7:
        return 0.60

    return 0.35


def _build_gemini_prompt(articles: list[dict], company: str) -> str:
    article_lines = []

    for index, article in enumerate(articles, start=1):
        article_lines.append(
            f"""
Article {index}
Title: {article.get("title") or "Unknown"}
Source: {article.get("source") or "Unknown"}
Published: {article.get("published_at") or "Unknown"}
URL: {article.get("url") or ""}
""".strip()
        )

    articles_text = "\n\n".join(article_lines)

    return f"""
The user entered the company name "{company}".

Treat this as an unverified company name. Use the supplied articles and
Indian telecom context to determine which company the user most likely
means.

Do not assume the identity solely from the entered name. Ignore foreign
companies, unrelated businesses, and similarly named organisations.

Do not invent a legal name, stock symbol, ownership information, company
metrics, or market events.

If the company cannot be identified reliably from the supplied evidence:

- Clearly state the identity uncertainty in the summary.
- Keep the confidence score low.
- Keep the market-impact score close to zero.
- Do not attribute unsupported news to the company.

Analyse current market developments relevant to the most likely Indian
telecom company represented by "{company}".

Use URL Context to open and analyse the supplied article URLs.

Your task is NOT to predict revenue directly. The application's statistical
forecasting model already predicts revenue using:

1. ARPU
2. Data customers/subscribers
3. Inflation
4. Tariff hike

Your job is only to quantify how the current external news environment may
cause next-quarter revenue to perform above or below the historical model's
baseline forecast.

Return a Market Impact Score from -100 to +100:

-100 = exceptionally damaging external environment
-60 = strongly negative
-20 = mildly negative
0 = neutral or insufficient evidence
+20 = mildly positive
+60 = strongly positive
+100 = exceptionally favourable external environment

Important rules:

1. Base the score only on article pages that were successfully retrieved.
2. Do not treat general stock-price movement as direct evidence of revenue
   growth.
3. Prioritise developments affecting pricing, tariffs, ARPU, subscribers,
   customer demand, competition, regulation, spectrum, network expansion,
   inflation and operating conditions.
4. Ignore irrelevant information.
5. Do not invent facts from inaccessible or paywalled pages.
6. Use conservative scoring. Scores above +70 or below -70 should be rare.
7. The score represents expected next-quarter REVENUE impact, not share-price
   sentiment.
8. Give every article an individual revenue impact score from -1 to +1.
9. Confidence must reflect the quality, relevance and number of successfully
   retrieved sources.

Articles:

{articles_text}
""".strip()


def _gemini_response_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "market_score": {
                "type": "number",
                "description": (
                    "Overall next-quarter revenue impact score from -100 to 100."
                ),
            },
            "confidence": {
                "type": "number",
                "description": "Confidence percentage from 0 to 100.",
            },
            "sentiment": {
                "type": "number",
                "description": (
                    "Overall revenue-oriented sentiment from -100 to 100."
                ),
            },
            "relevance": {
                "type": "number",
                "description": (
                    "Average relevance of successfully analysed sources, 0 to 100."
                ),
            },
            "importance": {
                "type": "number",
                "description": (
                    "Average business importance of the analysed events, 0 to 100."
                ),
            },
            "summary": {
                "type": "string",
                "description": "Concise explanation of the overall score.",
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
            },
            "opportunities": {
                "type": "array",
                "items": {"type": "string"},
            },
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "impact_score": {
                            "type": "number",
                            "description": (
                                "Expected revenue impact from -1 to 1."
                            ),
                        },
                        "reason": {
                            "type": "string",
                            "description": (
                                "Brief reason for the article impact score."
                            ),
                        },
                    },
                    "required": [
                        "url",
                        "impact_score",
                        "reason",
                    ],
                },
            },
        },
        "required": [
            "market_score",
            "confidence",
            "sentiment",
            "relevance",
            "importance",
            "summary",
            "risks",
            "opportunities",
            "articles",
        ],
    }


def _generate_gemini_market_result(
    articles: list[dict],
    company: str,
) -> tuple[dict, list[dict]]:
    api_key = get_gemini_api_key()

    if not api_key:
        raise NewsAPIError(
            "GEMINI_API_KEY is missing. Add it to Streamlit Secrets "
            "or your local .env file."
        )

    urls = [
        article.get("url")
        for article in articles
        if article.get("url")
    ]

    if not urls:
        raise NewsAPIError(
            "No valid article URLs were available for Gemini analysis."
        )

    client = genai.Client(api_key=api_key)
    prompt = _build_gemini_prompt(articles, company)

    response = None
    selected_model_id = None
    selected_model_name = None
    unavailable_models = []
    primary_retry_at = None

    for model_id, model_name in GEMINI_MODELS:
        blocked_until = _active_model_cooldown(model_id)

        if blocked_until:
            unavailable_models.append(model_name)
            if model_id == GEMINI_MODELS[0][0]:
                primary_retry_at = blocked_until
            continue

        model_hit_quota = False

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[
                            {"url_context": {}},
                        ],
                        response_mime_type="application/json",
                        response_schema=_gemini_response_schema(),
                        temperature=0.1,
                    ),
                )
                selected_model_id = model_id
                selected_model_name = model_name
                break

            except ServerError as exc:
                if attempt == 2:
                    raise NewsAPIError(
                        "Gemini is temporarily unavailable due to high demand. "
                        "Please refresh and try again."
                    ) from exc

                time.sleep(5 * (attempt + 1))

            except Exception as exc:
                if _is_quota_error(exc):
                    blocked_until = _block_model_after_quota_error(
                        model_id,
                        exc,
                    )
                    unavailable_models.append(model_name)
                    model_hit_quota = True

                    if model_id == GEMINI_MODELS[0][0]:
                        primary_retry_at = blocked_until

                    break

                raise NewsAPIError(
                    f"Gemini market analysis failed: {exc}"
                ) from exc

        if response is not None:
            break

        if not model_hit_quota:
            break

    if response is None or not response.text:
        if unavailable_models:
            raise NewsAPIError(
                "Gemini API quota has been reached for every configured "
                "analysis model."
            )

        raise NewsAPIError(
            "Gemini returned an empty market analysis."
        )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise NewsAPIError(
            "Gemini returned an invalid structured response."
        ) from exc

    result["_model_id"] = selected_model_id
    result["_model_used"] = selected_model_name
    result["_fallback_from"] = unavailable_models
    result["_primary_retry_at"] = (
        primary_retry_at.isoformat()
        if primary_retry_at
        else None
    )

    retrieval_results = []

    try:
        metadata = response.candidates[0].url_context_metadata
        url_metadata = metadata.url_metadata if metadata else []

        for item in url_metadata:
            retrieval_results.append(
                {
                    "url": item.retrieved_url,
                    "status": str(item.url_retrieval_status),
                }
            )
    except (AttributeError, IndexError, TypeError):
        retrieval_results = []

    return result, retrieval_results


def _bounded_number(
    value,
    minimum: float,
    maximum: float,
    default: float = 0.0,
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    return max(minimum, min(maximum, number))


def score_market_articles(
    articles: list[dict],
    company: str,
) -> dict:
    if not articles:
        return {
            "market_score": 0.0,
            "confidence": 0.0,
            "summary": "No relevant articles were available.",
            "risks": [],
            "opportunities": [],
            "breakdown": {
                "sentiment": 0.0,
                "relevance": 0.0,
                "importance": 0.0,
                "recency": 0.0,
            },
            "articles": [],
            "retrieval_results": [],
        }

    gemini_result, retrieval_results = _generate_gemini_market_result(
        articles=articles,
        company=company,
    )

    article_analysis_by_url = {
        str(item.get("url", "")).strip(): item
        for item in gemini_result.get("articles", [])
        if item.get("url")
    }

    scored_articles = []

    for article in articles:
        url = str(article.get("url") or "").strip()
        analysis = article_analysis_by_url.get(url, {})

        impact_score = _bounded_number(
            analysis.get("impact_score", 0.0),
            -1.0,
            1.0,
        )

        scored_articles.append(
            {
                **article,
                "impact_score": impact_score,
                "impact_reason": analysis.get(
                    "reason",
                    "Gemini did not assign a specific impact explanation.",
                ),
            }
        )

    scored_articles.sort(
        key=lambda article: abs(article["impact_score"]),
        reverse=True,
    )

    recency_scores = [
        _score_recency(article.get("published_at"))
        for article in articles
    ]

    average_recency = (
        sum(recency_scores) / len(recency_scores) * 100
        if recency_scores
        else 0.0
    )

    return {
        "market_score": _bounded_number(
            gemini_result.get("market_score"),
            -100.0,
            100.0,
        ),
        "confidence": _bounded_number(
            gemini_result.get("confidence"),
            0.0,
            100.0,
        ),
        "summary": str(gemini_result.get("summary") or ""),
        "risks": gemini_result.get("risks") or [],
        "opportunities": gemini_result.get("opportunities") or [],
        "breakdown": {
            "sentiment": _bounded_number(
                gemini_result.get("sentiment"),
                -100.0,
                100.0,
            ),
            "relevance": _bounded_number(
                gemini_result.get("relevance"),
                0.0,
                100.0,
            ),
            "importance": _bounded_number(
                gemini_result.get("importance"),
                0.0,
                100.0,
            ),
            "recency": average_recency,
        },
        "articles": scored_articles,
        "retrieval_results": retrieval_results,
        "model_id": gemini_result.get("_model_id"),
        "model_used": gemini_result.get("_model_used"),
        "fallback_from": gemini_result.get("_fallback_from") or [],
        "primary_retry_at": gemini_result.get("_primary_retry_at"),
    }


def fetch_external_news(
    company: str,
    page_size: int = 50,
    keep_top: int = 15,
) -> list[dict]:
    """
    Fetch the last 3 days of India-related telecom, economic,
    regulatory, and geopolitical news.

    The search remains broad. Only obviously irrelevant content is removed,
    then results are ranked and the top articles are retained.
    """
    api_key = get_news_api_key()

    if not api_key:
        raise NewsAPIError(
            "NEWS_API_KEY is missing. Add it to Streamlit Secrets "
            "or your local .env file."
        )

    from_date = datetime.now() - timedelta(days=3)

    clean_company = re.sub(
        r'[^a-zA-Z0-9 &.\-]',
        " ",
        str(company),
    )

    clean_company = re.sub(
        r"\s+",
        " ",
        clean_company,
    ).strip()

    company_search = (
        f'OR "{clean_company}"'
        if clean_company
        else ""
    )

    query = (
        f'(India AND (telecom OR Airtel OR Jio OR "Vodafone Idea" '
        f'OR TRAI OR spectrum OR tariff OR 5G {company_search})) '
        f'OR '
        f'(India AND (inflation OR GDP OR economy OR "repo rate" '
        f'OR RBI OR rupee OR "oil prices")) '
        f'OR '
        f'(India AND (war OR conflict OR sanctions OR geopolitical))'
    )

    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(page_size, 100),
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            NEWS_API_URL,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NewsAPIError(f"Could not fetch news: {exc}") from exc

    payload = response.json()

    if payload.get("status") != "ok":
        raise NewsAPIError(
            payload.get("message", "NewsAPI returned an error.")
        )

    clean_articles = []

    for article in payload.get("articles", []):
        title = article.get("title")

        if not title or title == "[Removed]":
            continue

        clean_article = {
            "title": title,
            "description": article.get("description") or "",
            "source": article.get("source", {}).get(
                "name", "Unknown source"
            ),
            "published_at": article.get("publishedAt"),
            "url": article.get("url"),
        }

        text = _normalise_text(clean_article)

        if _is_obviously_irrelevant(text):
            continue

        clean_article["retrieval_relevance"] = (
            _retrieval_relevance_score(
            text,
            company,
)
        )
        clean_articles.append(clean_article)

    clean_articles = _deduplicate_articles(clean_articles)

    clean_articles.sort(
        key=lambda article: (
            article["retrieval_relevance"],
            article.get("published_at") or "",
        ),
        reverse=True,
    )

    return clean_articles[:keep_top]