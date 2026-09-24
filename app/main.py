from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator

from app.store import (
    DuplicateEdgeError,
    DuplicateNodeError,
    EdgeNotFoundError,
    NoPathError,
    NodeNotFoundError,
    store,
)

app = FastAPI(title="Network Route Optimization")


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Name is required")
        return name


class NodeResponse(BaseModel):
    id: int
    name: str


class EdgeCreate(BaseModel):
    source: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    latency: float = Field(..., gt=0)

    @field_validator("source", "destination")
    @classmethod
    def endpoint_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Source/destination is required")
        return name


class EdgeResponse(BaseModel):
    id: int
    source: str
    destination: str
    latency: float


class RouteRequest(BaseModel):
    source: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)

    @field_validator("source", "destination")
    @classmethod
    def endpoint_must_not_be_blank(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Source/destination is required")
        return name


class RouteResponse(BaseModel):
    total_latency: float
    path: list[str]


class HistoryRecord(BaseModel):
    id: int
    source: str
    destination: str
    total_latency: float
    path: list[str]
    created_at: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    fields = {error["loc"][-1] for error in exc.errors() if error.get("loc")}

    if fields & {"limit", "date_from", "date_to"}:
        detail = "Invalid query parameters"
    elif fields & {"source", "destination"}:
        detail = "Source/destination missing"
    elif "latency" in fields:
        detail = "Latency must be greater than 0"
    elif "name" in fields:
        detail = "Name missing or invalid"
    else:
        detail = "Invalid request body"

    return JSONResponse(status_code=400, content={"detail": detail})


@app.post("/nodes", response_model=NodeResponse, status_code=201)
def add_node(payload: NodeCreate) -> NodeResponse:
    try:
        return store.add_node(payload.name)
    except DuplicateNodeError:
        raise HTTPException(status_code=400, detail="Name already exists")


@app.get("/nodes", response_model=list[NodeResponse])
def list_nodes() -> list[NodeResponse]:
    return store.list_nodes()


@app.delete("/nodes/{node_id}", status_code=204)
def delete_node(node_id: int) -> Response:
    try:
        store.delete_node(node_id)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail="Node not found")
    return Response(status_code=204)


@app.post("/edges", response_model=EdgeResponse, status_code=201)
def add_edge(payload: EdgeCreate) -> EdgeResponse:
    try:
        return store.add_edge(payload.source, payload.destination, payload.latency)
    except NodeNotFoundError:
        raise HTTPException(status_code=400, detail="Nodes not found")
    except DuplicateEdgeError:
        raise HTTPException(status_code=400, detail="Duplicate edge")


@app.get("/edges", response_model=list[EdgeResponse])
def list_edges() -> list[EdgeResponse]:
    return store.list_edges()


@app.delete("/edges/{edge_id}", status_code=204)
def delete_edge(edge_id: int) -> Response:
    try:
        store.delete_edge(edge_id)
    except EdgeNotFoundError:
        raise HTTPException(status_code=404, detail="Edge not found")
    return Response(status_code=204)


@app.post("/routes/shortest", response_model=RouteResponse)
def get_shortest_route(payload: RouteRequest) -> RouteResponse:
    try:
        return store.shortest_path(payload.source, payload.destination)
    except NodeNotFoundError:
        raise HTTPException(status_code=400, detail="Invalid or non-existent nodes")
    except NoPathError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.get("/routes/history", response_model=list[HistoryRecord])
def get_route_history(
    source: str | None = None,
    destination: str | None = None,
    limit: int | None = Query(default=None, gt=0),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[HistoryRecord]:
    return store.list_history(
        source=source,
        destination=destination,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )
