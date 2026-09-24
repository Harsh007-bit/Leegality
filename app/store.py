from datetime import datetime, timezone
from heapq import heappop, heappush
from threading import Lock


class DuplicateNodeError(Exception):
    pass


class DuplicateEdgeError(Exception):
    pass


class NodeNotFoundError(Exception):
    pass


class EdgeNotFoundError(Exception):
    pass


class NoPathError(Exception):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_history(record: dict) -> dict:
    return {
        **record,
        "created_at": record["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class GraphStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._next_node_id = 1
        self._next_edge_id = 1
        self._next_history_id = 1
        self._nodes: dict[int, dict] = {}
        self._names: set[str] = set()
        self._edges: dict[int, dict] = {}
        self._edge_keys: set[tuple[str, str]] = set()
        self._adjacency: dict[str, list[tuple[str, float]]] = {}
        self._history: list[dict] = []

    def add_node(self, name: str) -> dict:
        with self._lock:
            if name in self._names:
                raise DuplicateNodeError(f"Node '{name}' already exists")

            node = {"id": self._next_node_id, "name": name}
            self._nodes[self._next_node_id] = node
            self._names.add(name)
            self._adjacency[name] = []
            self._next_node_id += 1
            return dict(node)

    def list_nodes(self) -> list[dict]:
        with self._lock:
            return [dict(node) for node in self._nodes.values()]

    def delete_node(self, node_id: int) -> None:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                raise NodeNotFoundError(f"Node {node_id} not found")

            name = node["name"]
            stale_ids = [
                edge_id
                for edge_id, edge in self._edges.items()
                if edge["source"] == name or edge["destination"] == name
            ]
            for edge_id in stale_ids:
                edge = self._edges.pop(edge_id)
                self._edge_keys.discard((edge["source"], edge["destination"]))

            del self._nodes[node_id]
            self._names.discard(name)
            self._adjacency.pop(name, None)
            for source, neighbors in self._adjacency.items():
                self._adjacency[source] = [
                    (neighbor, latency)
                    for neighbor, latency in neighbors
                    if neighbor != name
                ]

    def add_edge(self, source: str, destination: str, latency: float) -> dict:
        with self._lock:
            missing = [name for name in (source, destination) if name not in self._names]
            if missing:
                raise NodeNotFoundError(
                    f"Node(s) not found: {', '.join(missing)}"
                )

            key = (source, destination)
            if key in self._edge_keys:
                raise DuplicateEdgeError(
                    f"Edge from '{source}' to '{destination}' already exists"
                )

            edge = {
                "id": self._next_edge_id,
                "source": source,
                "destination": destination,
                "latency": latency,
            }
            self._edges[self._next_edge_id] = edge
            self._edge_keys.add(key)
            self._adjacency[source].append((destination, latency))
            self._next_edge_id += 1
            return dict(edge)

    def list_edges(self) -> list[dict]:
        with self._lock:
            return [dict(edge) for edge in self._edges.values()]

    def delete_edge(self, edge_id: int) -> None:
        with self._lock:
            edge = self._edges.pop(edge_id, None)
            if edge is None:
                raise EdgeNotFoundError(f"Edge {edge_id} not found")

            self._edge_keys.discard((edge["source"], edge["destination"]))
            self._adjacency[edge["source"]] = [
                (neighbor, latency)
                for neighbor, latency in self._adjacency[edge["source"]]
                if neighbor != edge["destination"]
            ]

    def shortest_path(self, source: str, destination: str) -> dict:
        with self._lock:
            missing = [name for name in (source, destination) if name not in self._names]
            if missing:
                raise NodeNotFoundError(
                    f"Node(s) not found: {', '.join(missing)}"
                )

            if source == destination:
                result = {"total_latency": 0.0, "path": [source]}
                self._record_history(source, destination, result)
                return result

            distances = {name: float("inf") for name in self._names}
            previous: dict[str, str | None] = {name: None for name in self._names}
            distances[source] = 0.0
            heap: list[tuple[float, str]] = [(0.0, source)]

            while heap:
                current_distance, current = heappop(heap)
                if current_distance > distances[current]:
                    continue
                if current == destination:
                    break

                for neighbor, latency in self._adjacency[current]:
                    candidate = current_distance + latency
                    if candidate < distances[neighbor]:
                        distances[neighbor] = candidate
                        previous[neighbor] = current
                        heappush(heap, (candidate, neighbor))

            if distances[destination] == float("inf"):
                raise NoPathError(
                    f"No path exists between {source} and {destination}"
                )

            path = [destination]
            node = destination
            while node != source:
                node = previous[node]
                path.append(node)
            path.reverse()

            result = {"total_latency": distances[destination], "path": path}
            self._record_history(source, destination, result)
            return result

    def list_history(
        self,
        source: str | None = None,
        destination: str | None = None,
        limit: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict]:
        with self._lock:
            records = self._history

            if source:
                records = [record for record in records if record["source"] == source]
            if destination:
                records = [
                    record for record in records if record["destination"] == destination
                ]
            if date_from:
                start = _as_utc(date_from)
                records = [record for record in records if record["created_at"] >= start]
            if date_to:
                end = _as_utc(date_to)
                records = [record for record in records if record["created_at"] <= end]

            records = list(reversed(records))
            if limit is not None:
                records = records[:limit]
            return [_serialize_history(record) for record in records]

    def _record_history(self, source: str, destination: str, result: dict) -> None:
        self._history.append(
            {
                "id": self._next_history_id,
                "source": source,
                "destination": destination,
                "total_latency": result["total_latency"],
                "path": list(result["path"]),
                "created_at": _utc_now(),
            }
        )
        self._next_history_id += 1


store = GraphStore()
