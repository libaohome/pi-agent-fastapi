import json
from pathlib import Path
from uuid import uuid4

import networkx as nx

from app.config import get_settings


class KnowledgeGraphService:
    def __init__(self, user_id: str, graph_id: str | None = None):
        self.user_id = user_id
        self.graph_id = graph_id or str(uuid4())
        settings = get_settings()
        self.base_dir = Path(settings.knowledge_graph_dir) / user_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.graph_path = self.base_dir / f"{self.graph_id}.json"

    def _load(self) -> nx.MultiDiGraph:
        if self.graph_path.exists():
            with self.graph_path.open(encoding="utf-8") as f:
                data = json.load(f)
            return nx.node_link_graph(data, directed=True, multigraph=True)
        return nx.MultiDiGraph()

    def _save(self, graph: nx.MultiDiGraph) -> None:
        data = nx.node_link_data(graph)
        with self.graph_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_graphs(self) -> list[dict]:
        graphs = []
        for path in self.base_dir.glob("*.json"):
            graphs.append(
                {
                    "id": path.stem,
                    "node_count": len(self._load_from_path(path).nodes),
                    "edge_count": len(self._load_from_path(path).edges),
                }
            )
        return graphs

    @staticmethod
    def _load_from_path(path: Path) -> nx.MultiDiGraph:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        return nx.node_link_graph(data, directed=True, multigraph=True)

    def add_triple(self, subject: str, predicate: str, obj: str, **attrs) -> dict:
        graph = self._load()
        for node in (subject, obj):
            if not graph.has_node(node):
                graph.add_node(node, id=node)
        graph.add_edge(subject, obj, key=predicate, predicate=predicate, **attrs)
        self._save(graph)
        return {"subject": subject, "predicate": predicate, "object": obj}

    def query_neighbors(self, entity: str, depth: int = 1) -> dict:
        graph = self._load()
        if entity not in graph:
            return {"entity": entity, "neighbors": []}
        nodes = nx.single_source_shortest_path_length(graph, entity, cutoff=depth)
        edges = []
        for u, v, data in graph.edges(data=True):
            if u in nodes and v in nodes:
                edges.append({"source": u, "target": v, "predicate": data.get("predicate")})
        return {"entity": entity, "depth": depth, "nodes": list(nodes.keys()), "edges": edges}

    def export_graph(self) -> dict:
        graph = self._load()
        return nx.node_link_data(graph)
