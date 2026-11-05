"""Fredagsbar API: events og tilmeldinger.

Kør:
    uv run api.py

Prøv i Postman (GET):
    http://127.0.0.1:5000/events
    http://127.0.0.1:5000/events/1

Prøv i Postman (POST) med Body -> raw -> JSON:
    http://127.0.0.1:5000/events
    {"title": "Beerpong", "date": "2026-12-04", "capacity": 8}

    http://127.0.0.1:5000/events/1/signups
    {"name": "Dave"}

Prøv i Postman (DELETE):
    http://127.0.0.1:5000/events/1/signups/Anna
    http://127.0.0.1:5000/events/1
"""

import os

from flask import Flask, request

app = Flask(__name__)

events = [
    {
        "id": 1,
        "title": "Quizaften",
        "date": "2026-11-13",
        "capacity": 3,
        "participants": ["Anna", "Bodil"],
    },
    {
        "id": 2,
        "title": "Brætspilsaften",
        "date": "2026-11-20",
        "capacity": 10,
        "participants": [],
    },
    {
        "id": 3,
        "title": "Beerpong-turnering",
        "date": "2026-11-27",
        "capacity": 2,
        "participants": ["Clara", "David"],
    },
]


def find_event(event_id):
    for event in events:
        if event["id"] == event_id:
            return event
    return None


@app.get("/events")
def get_events():
    return events


@app.get("/events/<int:event_id>")
def get_event(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event with id {event_id} not found"}, 404
    return event


@app.post("/events")
def create_event():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "Request body must be a JSON object"}, 400

    title = data.get("title")
    date = data.get("date")
    capacity = data.get("capacity")

    if not isinstance(title, str) or not title.strip():
        return {"error": "title is required"}, 400
    if not isinstance(date, str) or not date.strip():
        return {"error": "date is required"}, 400
    if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
        return {"error": "capacity must be a positive integer"}, 400

    new_event = {
        "id": max((e["id"] for e in events), default=0) + 1,
        "title": title.strip(),
        "date": date.strip(),
        "capacity": capacity,
        "participants": [],
    }
    events.append(new_event)
    return new_event, 201


@app.post("/events/<int:event_id>/signups")
def sign_up(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event with id {event_id} not found"}, 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "Request body must be a JSON object"}, 400

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return {"error": "name is required"}, 400
    name = name.strip()

    for participant in event["participants"]:
        if participant.lower() == name.lower():
            return {"error": f"{name} is already signed up"}, 409

    if len(event["participants"]) >= event["capacity"]:
        return {"error": "Event is full"}, 409

    event["participants"].append(name)
    return event, 201


@app.delete("/events/<int:event_id>/signups/<name>")
def cancel_signup(event_id, name):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event with id {event_id} not found"}, 404

    for participant in event["participants"]:
        if participant.lower() == name.strip().lower():
            event["participants"].remove(participant)
            return "", 204
    return {"error": f"{name} is not signed up for this event"}, 404


@app.delete("/events/<int:event_id>")
def delete_event(event_id):
    event = find_event(event_id)
    if event is None:
        return {"error": f"Event with id {event_id} not found"}, 404
    events.remove(event)
    return "", 204


if __name__ == "__main__":
    app.run(
        host=os.environ.get("API_HOST", "127.0.0.1"),
        port=5000,
        debug=os.environ.get("API_DEBUG", "1") == "1",
    )