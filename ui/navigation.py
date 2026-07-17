import streamlit as st


PAGES = [
    ("setup", "Forecast Setup"),
    ("ai", "AI Market Intelligence"),
    ("results", "Forecast Results"),
]


def go_to_page(page: str):
    valid_pages = {page_key for page_key, _ in PAGES}
    if page not in valid_pages:
        raise ValueError(f"Unknown page: {page}")
    st.session_state.current_page = page


def render_navigation():
    current_page = st.session_state.get("current_page", "setup")
    columns = st.columns(3)

    for column, (page_key, page_label) in zip(columns, PAGES):
        with column:
            if st.button(
                page_label,
                key=f"nav_{page_key}",
                type="primary" if current_page == page_key else "secondary",
                use_container_width=True,
            ):
                if page_key != current_page:
                    go_to_page(page_key)
                    st.rerun()

    st.divider()