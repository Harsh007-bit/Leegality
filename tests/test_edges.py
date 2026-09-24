from tests.conftest import create_edge, create_nodes


def test_add_edge_returns_201(client):
    create_nodes(client, "ServerA", "ServerB")

    response = create_edge(client, "ServerA", "ServerB", 12.5)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "source": "ServerA",
        "destination": "ServerB",
        "latency": 12.5,
    }


def test_add_edge_rejects_missing_source(client):
    create_nodes(client, "ServerB")

    response = client.post("/edges", json={"destination": "ServerB", "latency": 12.5})

    assert response.status_code == 400
    assert response.json()["detail"] == "Source/destination missing"


def test_add_edge_rejects_missing_destination(client):
    create_nodes(client, "ServerA")

    response = client.post("/edges", json={"source": "ServerA", "latency": 12.5})

    assert response.status_code == 400
    assert response.json()["detail"] == "Source/destination missing"


def test_add_edge_rejects_non_positive_latency(client):
    create_nodes(client, "ServerA", "ServerB")

    zero = create_edge(client, "ServerA", "ServerB", 0)
    negative = create_edge(client, "ServerA", "ServerB", -1)

    assert zero.status_code == 400
    assert negative.status_code == 400
    assert zero.json()["detail"] == "Latency must be greater than 0"


def test_add_edge_rejects_unknown_nodes(client):
    create_nodes(client, "ServerA")

    response = create_edge(client, "ServerA", "ServerZ", 3)

    assert response.status_code == 400
    assert response.json()["detail"] == "Nodes not found"


def test_add_edge_rejects_duplicate_edge(client):
    create_nodes(client, "ServerA", "ServerB")
    create_edge(client, "ServerA", "ServerB", 12.5)

    response = create_edge(client, "ServerA", "ServerB", 5)

    assert response.status_code == 400
    assert response.json()["detail"] == "Duplicate edge"


def test_reverse_edge_is_allowed(client):
    create_nodes(client, "ServerA", "ServerB")
    create_edge(client, "ServerA", "ServerB", 12.5)

    response = create_edge(client, "ServerB", "ServerA", 8)

    assert response.status_code == 201
    assert response.json()["id"] == 2


def test_list_edges_returns_all_edges(client):
    create_nodes(client, "ServerA", "ServerB")
    create_edge(client, "ServerA", "ServerB", 12.5)

    response = client.get("/edges")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "source": "ServerA",
            "destination": "ServerB",
            "latency": 12.5,
        }
    ]


def test_delete_edge_returns_204(client):
    create_nodes(client, "ServerA", "ServerB")
    create_edge(client, "ServerA", "ServerB", 12.5)

    response = client.delete("/edges/1")

    assert response.status_code == 204
    assert client.get("/edges").json() == []


def test_delete_edge_returns_404_when_missing(client):
    response = client.delete("/edges/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Edge not found"
