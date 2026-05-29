"""Navigator for building knowledge path."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""

    id: str
    label: str
    node_type: str  # concept, topic, insight, example
    description: str = ""
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeNavigator:
    """Build and navigate knowledge paths."""

    def __init__(self) -> None:
        self.nodes: Dict[str, KnowledgeNode] = {}

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        description: str = "",
        parent_id: Optional[str] = None,
    ) -> None:
        """Add a node to the knowledge graph."""
        node = KnowledgeNode(
            id=node_id,
            label=label,
            node_type=node_type,
            description=description,
            parent_id=parent_id,
        )

        # Update parent's children
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)

        self.nodes[node_id] = node

    def build_default_path(self) -> None:
        """Build default psychology analysis path."""
        # Level 1: Personality types
        self.add_node("personality", "性格类型", "concept")

        # Level 2: Behavior drivers
        self.add_node("behavior", "行为动机", "concept", parent_id="personality")

        # Level 3: Relationship patterns
        self.add_node("relationship", "关系模式", "concept", parent_id="behavior")

        # Level 4: Change opportunities
        self.add_node("change", "改变契机", "concept", parent_id="relationship")

    def get_path(self, node_id: str) -> List[str]:
        """Get path from root to node."""
        path = []
        current = node_id

        while current and current in self.nodes:
            path.append(self.nodes[current].label)
            current = self.nodes[current].parent_id

        path.reverse()
        return path

    def get_children(self, node_id: str) -> List[KnowledgeNode]:
        """Get children of a node."""
        if node_id not in self.nodes:
            return []

        child_ids = self.nodes[node_id].children
        return [self.nodes[cid] for cid in child_ids if cid in self.nodes]

    def to_markdown(self) -> str:
        """Generate markdown for the knowledge path."""
        lines = [
            "# 知识导航路径",
            "",
            "## 路径结构",
            "",
        ]

        # Start from root nodes
        roots = [n for n in self.nodes.values() if n.parent_id is None]

        for root in roots:
            lines.extend(self._render_tree(root, 0))

        return "\n".join(lines)

    def _render_tree(self, node: KnowledgeNode, depth: int) -> List[str]:
        """Render node as markdown tree."""
        prefix = "  " * depth
        line = f"{prefix}- {node.label}"

        if node.description:
            line += f": {node.description}"

        lines = [line]

        # Render children
        for child_id in node.children:
            if child_id in self.nodes:
                lines.extend(self._render_tree(self.nodes[child_id], depth + 1))

        return lines

    def export_json(self, path: Path) -> None:
        """Export navigator to JSON."""
        data = {
            node_id: {
                "label": node.label,
                "node_type": node.node_type,
                "description": node.description,
                "parent_id": node.parent_id,
                "children": node.children,
                "metadata": node.metadata,
            }
            for node_id, node in self.nodes.items()
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))