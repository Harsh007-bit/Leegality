from tests.conftest import create_nodes


def test_add_node_returns_201_with_id_and_name(client):
    response = client.post("/nodes", json={"name": "ServerA"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "ServerA"}


def test_add_node_increments_ids(client):
    first = client.post("/nodes", json={"name": "ServerA"})
    second = client.post("/nodes", json={"name": "ServerB"})

    assert first.json()["id"] == 1
    assert second.json() == {"id": 2, "name": "ServerB"}


def test_add_node_rejects_missing_name(client):
    response = client.post("/nodes", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Name missing or invalid"


def test_add_node_rejects_blank_name(client):
    response = client.post("/nodes", json={"name": "   "})

    assert response.status_code == 400


def test_add_node_rejects_duplicate_name(client):
    client.post("/nodes", json={"name": "ServerA"})
    response = client.post("/nodes", json={"name": "ServerA"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Name already exists"


def test_list_nodes_returns_all_nodes(client):
    create_nodes(client, "ServerA", "ServerB")

    response = client.get("/nodes")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "ServerA"},
        {"id": 2, "name": "ServerB"},
    ]


def test_delete_node_returns_204(client):
    create_nodes(client, "ServerA")

    response = client.delete("/nodes/1")

    assert response.status_code == 204
    assert client.get("/nodes").json() == []


def test_delete_node_returns_404_when_missing(client):
    response = client.delete("/nodes/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"


def test_delete_node_also_removes_connected_edges(client):
    create_nodes(client, "ServerA", "ServerB")
    client.post(
        "/edges",
        json={"source": "ServerA", "destination": "ServerB", "latency": 5},
    )

    client.delete("/nodes/1")

    assert client.get("/edges").json() == []
