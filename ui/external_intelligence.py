import streamlit as st

from models.core import (
    build_regression_forecast,
    predict_prophet_for_quarters,
)
from services.news_fetcher import NewsAPIError, fetch_external_news
from ui.navigation import go_to_page


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def get_cached_external_news():
    return fetch_external_news(page_size=30)


def generate_forecast(df, use_market_intelligence):
    # Read the permanent configuration saved by Forecast Setup.
    # Do not read widget keys here because Streamlit removes widget state
    # when the Setup page is no longer rendered.
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

    st.session_state["forecast_output"] = {
        "forecast_df": forecast_df,
        "approach": approach,
        "model_name": model_name,
        "target_period": target_period,
        "use_market_intelligence": use_market_intelligence,
    }

    return True


def render_external_intelligence(df):
    title_col, refresh_col = st.columns([4, 1])

    with title_col:
        st.subheader("AI Market Intelligence")
        st.caption(
            "Review relevant market developments before generating "
            "the forecast."
        )

    with refresh_col:
        st.write("")
        if st.button(
            "↻ Refresh",
            key="refresh_external_news",
            use_container_width=True,
        ):
            get_cached_external_news.clear()
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

        st.write(
            f"**{article_count} relevant articles** collected from telecom, "
            "government, economic, and geopolitical sources."
        )

        if articles:
            with st.expander(
                f"View collected articles ({article_count})",
                expanded=False,
            ):
                for index, article in enumerate(articles):
                    st.markdown(f"**{article['title']}**")
                    st.caption(
                        f"{article['source']} · "
                        f"{article['published_at'] or 'Date unavailable'}"
                    )

                    if article.get("description"):
                        st.write(article["description"])

                    if article.get("url"):
                        st.link_button(
                            "Read source",
                            article["url"],
                            key=f"article_link_{index}",
                        )

                    if index < article_count - 1:
                        st.divider()
        else:
            st.caption(
                "No relevant articles were found during this refresh."
            )

    except NewsAPIError as exc:
        st.error(str(exc))

    st.caption(
        "AI scoring is not applied yet. The generated result remains "
        "the base model forecast."
    )

    st.divider()

    back_col, spacer_col, generate_col = st.columns([1, 2, 1.4])

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
            if generate_forecast(
                df=df,
                use_market_intelligence=True,
            ):
                go_to_page("results")
                st.rerun()