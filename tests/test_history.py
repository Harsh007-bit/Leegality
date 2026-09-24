from datetime import datetime, timedelta, timezone

from tests.conftest import create_edge, create_nodes


def _seed_successful_queries(client):
    create_nodes(client, "ServerA", "ServerB", "ServerC", "ServerD")
    create_edge(client, "ServerA", "ServerB", 10.0)
    create_edge(client, "ServerB", "ServerD", 13.4)
    create_edge(client, "ServerB", "ServerC", 10.1)
    client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "ServerD"},
    )
    client.post(
        "/routes/shortest",
        json={"source": "ServerB", "destination": "ServerC"},
    )


def test_history_records_successful_shortest_queries(client):
    _seed_successful_queries(client)

    response = client.get("/routes/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 2
    assert data[0]["source"] == "ServerB"
    assert data[0]["destination"] == "ServerC"
    assert data[0]["total_latency"] == 10.1
    assert data[0]["path"] == ["ServerB", "ServerC"]
    assert data[0]["created_at"].endswith("Z")
    assert data[1]["path"] == ["ServerA", "ServerB", "ServerD"]
    assert data[1]["total_latency"] == 23.4


def test_history_skips_failed_queries(client):
    _seed_successful_queries(client)
    client.post(
        "/routes/shortest",
        json={"source": "ServerD", "destination": "ServerA"},
    )
    client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "Ghost"},
    )

    response = client.get("/routes/history")

    assert len(response.json()) == 2


def test_history_filters_by_source(client):
    _seed_successful_queries(client)

    response = client.get("/routes/history", params={"source": "ServerA"})

    assert [item["id"] for item in response.json()] == [1]


def test_history_filters_by_destination(client):
    _seed_successful_queries(client)

    response = client.get("/routes/history", params={"destination": "ServerC"})

    assert [item["id"] for item in response.json()] == [2]


def test_history_respects_limit(client):
    _seed_successful_queries(client)

    response = client.get("/routes/history", params={"limit": 1})

    assert [item["id"] for item in response.json()] == [2]


def test_history_filters_by_date_range(client):
    _seed_successful_queries(client)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    assert len(client.get("/routes/history", params={"date_from": past}).json()) == 2
    assert client.get("/routes/history", params={"date_to": past}).json() == []
    assert client.get("/routes/history", params={"date_from": future}).json() == []


def test_history_rejects_invalid_limit(client):
    response = client.get("/routes/history", params={"limit": 0})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid query parameters"
