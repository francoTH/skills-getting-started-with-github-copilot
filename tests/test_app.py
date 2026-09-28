from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    activity_name = "Soccer Club"
    email = "student@example.com"
    encoded_activity_name = quote(activity_name, safe="")

    response = client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_participant(client):
    activity_name = "Soccer Club"
    email = "student@example.com"
    encoded_activity_name = quote(activity_name, safe="")
    signup_url = f"/activities/{encoded_activity_name}/signup"
    params = {"email": email}

    assert client.post(signup_url, params=params).status_code == 200
    response = client.post(signup_url, params=params)

    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_removes_participant(client):
    activity_name = "Soccer Club"
    email = "student@example.com"
    encoded_activity_name = quote(activity_name, safe="")
    client.post(
        f"/activities/{encoded_activity_name}/signup",
        params={"email": email},
    )

    response = client.delete(
        f"/activities/{encoded_activity_name}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/participants",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    activity_name = "Soccer Club"
    encoded_activity_name = quote(activity_name, safe="")

    response = client.delete(
        f"/activities/{encoded_activity_name}/participants",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert "not signed up" in response.json()["detail"]