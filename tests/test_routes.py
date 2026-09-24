from tests.conftest import create_edge, create_nodes


def _seed_graph(client):
    create_nodes(client, "ServerA", "ServerB", "ServerC", "ServerD")
    create_edge(client, "ServerA", "ServerB", 10.0)
    create_edge(client, "ServerB", "ServerD", 13.4)
    create_edge(client, "ServerA", "ServerC", 50.0)
    create_edge(client, "ServerC", "ServerD", 50.0)


def test_shortest_route_returns_lowest_latency_path(client):
    _seed_graph(client)

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "ServerD"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_latency": 23.4,
        "path": ["ServerA", "ServerB", "ServerD"],
    }


def test_shortest_route_same_node_has_zero_latency(client):
    create_nodes(client, "ServerA")

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "ServerA"},
    )

    assert response.status_code == 200
    assert response.json() == {"total_latency": 0.0, "path": ["ServerA"]}


def test_shortest_route_returns_404_when_no_path(client):
    _seed_graph(client)

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerD", "destination": "ServerA"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "No path exists between ServerD and ServerA"
    }


def test_shortest_route_rejects_unknown_nodes(client):
    create_nodes(client, "ServerA")

    response = client.post(
        "/routes/shortest",
        json={"source": "ServerA", "destination": "Ghost"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or non-existent nodes"


def test_shortest_route_rejects_missing_destination(client):
    response = client.post("/routes/shortest", json={"source": "ServerA"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Source/destination missing"
