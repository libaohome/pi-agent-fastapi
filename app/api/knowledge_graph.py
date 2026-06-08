from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import AuthContext, get_current_user
from app.schemas.common import GraphQueryRequest, TripleRequest
from app.services.knowledge_graph import KnowledgeGraphService

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


def _service(user: AuthContext, graph_id: str | None = None) -> KnowledgeGraphService:
    return KnowledgeGraphService(user.user_id, graph_id)


@router.get("/graphs")
async def list_graphs(user: Annotated[AuthContext, Depends(get_current_user)]):
    return {"graphs": _service(user).list_graphs()}


@router.post("/triples")
async def add_triple(
    body: TripleRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    svc = _service(user, body.graph_id)
    triple = svc.add_triple(body.subject, body.predicate, body.obj)
    return {"graph_id": svc.graph_id, "triple": triple}


@router.post("/query")
async def query_graph(
    body: GraphQueryRequest,
    user: Annotated[AuthContext, Depends(get_current_user)],
):
    svc = _service(user, body.graph_id)
    return svc.query_neighbors(body.entity, body.depth)


@router.get("/export")
async def export_graph(
    user: Annotated[AuthContext, Depends(get_current_user)],
    graph_id: Annotated[str | None, Query()] = None,
):
    if not graph_id:
        raise HTTPException(400, detail="graph_id 必填")
    svc = _service(user, graph_id)
    return svc.export_graph()
