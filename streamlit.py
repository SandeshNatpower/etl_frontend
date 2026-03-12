import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="BBC Useful News", layout="wide")
st.title("BBC News Viewer")
st.caption("Powered by FastAPI + PostgreSQL")

# -----------------------------
# API helper functions
# -----------------------------
def get_news(useful_only=None, limit=20):
    try:
        params = {"limit": limit}
        if useful_only is not None:
            params["useful_only"] = useful_only

        response = requests.get(f"{API_BASE_URL}/news/", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch news: {e}")
        return []


def update_useful_news(news_id: int, useful_news: bool):
    try:
        payload = {"useful_news": useful_news}
        response = requests.put(
            f"{API_BASE_URL}/news/{news_id}/like",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        return False, str(e)


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")
limit = st.sidebar.slider("Number of articles", min_value=5, max_value=100, value=20, step=5)

filter_option = st.sidebar.radio(
    "Show articles",
    options=["All", "Useful only", "Not useful only"]
)

if filter_option == "All":
    useful_only = None
elif filter_option == "Useful only":
    useful_only = True
else:
    useful_only = False

refresh = st.sidebar.button("Refresh")

# -----------------------------
# Session state for refresh
# -----------------------------
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0

if refresh:
    st.session_state.refresh_counter += 1

# -----------------------------
# Fetch data
# -----------------------------
news_data = get_news(useful_only=useful_only, limit=limit)

st.subheader(f"Articles found: {len(news_data)}")

# -----------------------------
# Render articles
# -----------------------------
for idx, article in enumerate(news_data):
    news_id = article.get("id")
    title = article.get("title", "No title")
    summary = article.get("summary", "")
    source_name = article.get("source_name", "")
    published_ts = article.get("published_ts", "")
    link = article.get("link", "")
    useful_news = article.get("useful_news", False)
    can_update = news_id is not None
    button_suffix = f"{news_id}_{idx}" if can_update else f"missing_id_{idx}"

    with st.container(border=True):
        col1, col2 = st.columns([8, 2])

        with col1:
            st.markdown(f"### {title}")
            st.write(f"**Source:** {source_name}")
            st.write(f"**Published:** {published_ts}")
            if summary:
                st.write(summary)
            if link:
                st.markdown(f"[Read full article]({link})")

        with col2:
            st.write(f"**ID:** {news_id}")
            st.write(f"**Useful:** {useful_news}")
            if not can_update:
                st.caption("This article has no ID, so update is disabled.")

            selected_status = st.selectbox(
                "Set useful status",
                options=["Useful", "Not useful"],
                index=0 if useful_news else 1,
                key=f"status_{button_suffix}",
                disabled=not can_update,
            )

            if st.button("Update", key=f"update_{button_suffix}", disabled=not can_update):
                selected_useful_news = selected_status == "Useful"
                success, result = update_useful_news(news_id, selected_useful_news)
                if success:
                    st.success("News updated successfully")
                    st.rerun()
                else:
                    st.error(result)