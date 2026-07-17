import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"


class NewsAPIError(Exception):
    """Raised when news collection fails."""


def fetch_external_news(page_size: int = 30) -> list[dict]:
    """
    Fetch recent India-related telecom, economic, regulatory,
    and geopolitical news.
    """

    if not NEWS_API_KEY:
        raise NewsAPIError(
            "NEWS_API_KEY is missing. Add it to your .env file."
        )

    yesterday = datetime.now() - timedelta(days=1)

    query = (
        '(India AND (telecom OR Airtel OR Jio OR "Vodafone Idea" '
        'OR TRAI OR spectrum OR tariff)) '
        'OR '
        '(India AND (inflation OR GDP OR economy OR "repo rate" '
        'OR rupee OR "oil prices")) '
        'OR '
        '(India AND (war OR conflict OR sanctions OR geopolitical))'
    )

    params = {
        "q": query,
        "from": yesterday.strftime("%Y-%m-%d"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
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

        clean_articles.append(
            {
                "title": title,
                "description": article.get("description") or "",
                "source": article.get("source", {}).get(
                    "name", "Unknown source"
                ),
                "published_at": article.get("publishedAt"),
                "url": article.get("url"),
            }
        )

    return clean_articles