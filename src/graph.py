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
        Uses a try-except block to work on ANY NetworkX version.
        """
        try:
            # 1. Try the MODERN way (NetworkX 3.4+)
            # We add '# type: ignore' to stop Pylance from complaining if it thinks we are on an old version.
            data = nx.node_link_data(
                self.graph,
                source="source",
                target="target",
                name="id",
                edges="links"  # type: ignore
            )
        except TypeError:
            # 2. Fallback to the LEGACY way (NetworkX < 3.4)
            # This runs if the user has an old version installed.
            data = nx.node_link_data(
                self.graph,
                source="source",
                target="target",
                name="id"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Knowledge Graph saved to {output_path}")
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
