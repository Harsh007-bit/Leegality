import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


@pytest.fixture(autouse=True)
def reset_store():
    store._next_node_id = 1
    store._next_edge_id = 1
    store._next_history_id = 1
    store._nodes.clear()
    store._names.clear()
    store._edges.clear()
    store._edge_keys.clear()
    store._adjacency.clear()
    store._history.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def create_nodes(client: TestClient, *names: str) -> None:
    for name in names:
        response = client.post("/nodes", json={"name": name})
        assert response.status_code == 201


def create_edge(client: TestClient, source: str, destination: str, latency: float):
    return client.post(
        "/edges",
        json={"source": source, "destination": destination, "latency": latency},
    )
