import os
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

import httpx
import streamlit as st


class FredagsbarClient:

    def __init__(self, base_url: str | None = None, timeout: float = 2.0) -> None:
        self._client = httpx.Client(
            base_url=base_url or os.getenv("API_URL", "http://127.0.0.1:5000"),
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()

    def list_events(self) -> list[dict[str, Any]]:
        return self._request("GET", "/events")

    def create_event(self, title: str, date: str, capacity: int) -> dict[str, Any]:
        return self._request(
            "POST", "/events", json={"title": title, "date": date, "capacity": capacity}
        )

    def sign_up(self, event_id: int, name: str) -> dict[str, Any]:
        return self._request("POST", f"/events/{event_id}/signups", json={"name": name})

    def cancel_signup(self, event_id: int, name: str) -> None:
        self._request("DELETE", f"/events/{event_id}/signups/{quote(name, safe='')}")


st.set_page_config(page_title="Fredagsbar")
st.title("Fredagsbar")
st.write("Se events, tilmeld dig og opret nye events.")


@st.cache_resource
def get_api_client() -> FredagsbarClient:
    return FredagsbarClient(timeout=2.0)


client = get_api_client()


def report_api_error(error: Exception) -> None:
    if isinstance(error, httpx.HTTPStatusError):
        try:
            body = error.response.json()
            details = body.get("error", body) if isinstance(body, dict) else body
        except ValueError:
            details = error.response.text
        st.error(f"API-fejl ({error.response.status_code}): {details}")
    elif isinstance(error, httpx.TimeoutException):
        st.error("API'en svarede ikke inden for tidsgrænsen.")
    elif isinstance(error, httpx.ConnectError):
        st.error("Kunne ikke kontakte API'en. Kontrollér, at api.py kører.")
    elif isinstance(error, httpx.RequestError):
        st.error(f"HTTP-kaldet fejlede: {error}")
    else:
        raise error


def run_action(
    action: Callable[[], Any],
    success_message: str | None = None,
) -> tuple[bool, Any]:
    try:
        result = action()
    except (httpx.HTTPStatusError, httpx.RequestError) as error:
        report_api_error(error)
        return False, None
    if success_message:
        st.session_state["flash"] = success_message
    return True, result


flash = st.session_state.pop("flash", None)
if flash:
    st.success(flash)

my_name = st.sidebar.text_input("Dit navn", key="my_name").strip()

loaded, events = run_action(client.list_events)
if not loaded:
    st.stop()


st.subheader("Events")
if not events:
    st.info("Der er ingen events endnu.")
else:
    overview = [
        {
            "Titel": event["title"],
            "Dato": event["date"],
            "Antal tilmeldte": len(event["participants"]),
            "Ledige pladser": event["capacity"] - len(event["participants"]),
        }
        for event in events
    ]
    st.dataframe(overview, hide_index=True)

    st.subheader("Tilmeld og afmeld")
    events_by_id = {event["id"]: event for event in events}
    selected_id = st.selectbox(
        "Vælg event",
        options=list(events_by_id),
        format_func=lambda event_id: f"{events_by_id[event_id]['title']} ({events_by_id[event_id]['date']})",
    )
    selected = events_by_id[selected_id]
    free_spots = selected["capacity"] - len(selected["participants"])
    is_full = free_spots <= 0

    st.write(f"**Deltagere** ({len(selected['participants'])} af {selected['capacity']})")
    if not selected["participants"]:
        st.caption("Ingen er tilmeldt endnu.")
    for participant in selected["participants"]:
        st.text(f"• {participant}")
    if is_full:
        st.warning("Eventet er fuldt.")

    sign_up_col, cancel_col = st.columns(2)
    if sign_up_col.button("Tilmeld mig", disabled=is_full):
        succeeded, _ = run_action(
            lambda: client.sign_up(selected_id, my_name),
            f"{my_name} er tilmeldt {selected['title']}.",
        )
        if succeeded:
            st.rerun()
    if cancel_col.button("Afmeld mig"):
        succeeded, _ = run_action(
            lambda: client.cancel_signup(selected_id, my_name),
            f"{my_name} er afmeldt {selected['title']}.",
        )
        if succeeded:
            st.rerun()

with st.form("create_event_form"):
    st.subheader("Opret event")
    title = st.text_input("Titel")
    date = st.date_input("Dato")
    capacity = st.number_input("Antal pladser", min_value=1, value=10, step=1)
    submitted = st.form_submit_button("Opret event")

if submitted:
    succeeded, _ = run_action(
        lambda: client.create_event(title, str(date), capacity),
        "Eventet er oprettet.",
    )
    if succeeded:
        st.rerun()