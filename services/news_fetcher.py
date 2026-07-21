import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


def _retrieval_relevance_score(text: str) -> float:
    """
    Rank rather than hard-filter.

    Telecom articles rank highest, but broader economic and geopolitical
    developments remain eligible because they can still affect revenue.
    """
    score = 0.0

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
You are analysing current market developments for {company}, an Indian
subscription-based telecom business.

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

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
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
            break

        except ServerError as exc:
            if attempt == 2:
                raise NewsAPIError(
                    "Gemini is temporarily unavailable due to high demand. "
                    "Please refresh and try again."
                ) from exc

            time.sleep(5 * (attempt + 1))

        except Exception as exc:
            raise NewsAPIError(
                f"Gemini market analysis failed: {exc}"
            ) from exc

    if response is None or not response.text:
        raise NewsAPIError(
            "Gemini returned an empty market analysis."
        )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise NewsAPIError(
            "Gemini returned an invalid structured response."
        ) from exc

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
    }


def fetch_external_news(
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

    query = (
        '(India AND (telecom OR Airtel OR Jio OR "Vodafone Idea" '
        'OR TRAI OR spectrum OR tariff OR 5G)) '
        'OR '
        '(India AND (inflation OR GDP OR economy OR "repo rate" '
        'OR RBI OR rupee OR "oil prices")) '
        'OR '
        '(India AND (war OR conflict OR sanctions OR geopolitical))'
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
            _retrieval_relevance_score(text)
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