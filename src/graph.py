import networkx as nx
import json
import os


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, name: str, file_path: str, kind: int):
        node_id = f"{file_path}::{name}"
        human_kind = self._map_kind(kind)

        self.graph.add_node(
            node_id,
            label=name,
            type=human_kind,
            filepath=file_path
        )

        if not self.graph.has_node(file_path):
            self.graph.add_node(
                file_path,
                label=os.path.basename(file_path),
                type="File"
            )

        self.graph.add_edge(file_path, node_id, relation="defines")

    def save(self, output_path: str):
        """
        Exports the graph to a JSON file.
        Manual serialization to avoid NetworkX version-specific API changes.
        """
        data = self._to_node_link_data()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"OK: Knowledge Graph saved to {output_path}")
        print(f"   - Nodes: {self.graph.number_of_nodes()}")
        print(f"   - Edges: {self.graph.number_of_edges()}")

    def _map_kind(self, kind: int) -> str:
        mapping = {
            1: "File", 2: "Module", 3: "Namespace", 4: "Package",
            5: "Class", 6: "Method", 7: "Property", 8: "Field",
            9: "Constructor", 10: "Enum", 11: "Interface",
            12: "Function", 13: "Variable", 14: "Constant",
            15: "String", 16: "Number", 17: "Boolean", 18: "Array",
        }
        return mapping.get(kind, "Unknown")

    def _to_node_link_data(self) -> dict:
        graph = self.graph
        data = {
            "directed": graph.is_directed(),
            "multigraph": graph.is_multigraph(),
            "graph": dict(graph.graph),
            "nodes": [],
            "links": [],
        }

        for node_id, attrs in graph.nodes(data=True):
            node_entry = {"id": node_id}
            if attrs:
                node_entry.update(attrs)
            data["nodes"].append(node_entry)

        if graph.is_multigraph():
            for source, target, key, attrs in graph.edges(keys=True, data=True):
                link_entry = {"source": source, "target": target, "key": key}
                if attrs:
                    link_entry.update(attrs)
                data["links"].append(link_entry)
        else:
            for source, target, attrs in graph.edges(data=True):
                link_entry = {"source": source, "target": target}
                if attrs:
                    link_entry.update(attrs)
                data["links"].append(link_entry)

        return data
