"""Indexer for generating skill indices."""
import json
from pathlib import Path
from typing import Any, Dict, List

from person_fenxi_core.models import Chunk, Document, Skill


class SkillIndexer:
    """Generate skill indices from indexed documents."""

    def __init__(self) -> None:
        self.topics: List[Dict[str, Any]] = []

    def index_document(self, doc: Document, chunks: List[Chunk]) -> Dict[str, Any]:
        """Index a document and its chunks."""
        # Extract topics from chunks
        topic_list = self._extract_topics(chunks)

        entry = {
            "document_id": doc.id,
            "title": doc.title,
            "topic_count": len(topic_list),
            "topics": topic_list,
            "chunk_count": len(chunks),
        }

        self.topics.append(entry)
        return entry

    def _extract_topics(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Extract topics from chunks."""
        topics = []
        for chunk in chunks:
            # Simple extraction based on section titles
            section = chunk.metadata.get("section_title", "")
            if section and section != "全文":
                topics.append({
                    "section": section,
                    "chunk_id": chunk.id,
                })
        return topics

    def generate_skill_index(self) -> str:
        """Generate INDEX.md content."""
        lines = [
            "# 知识库索引",
            "",
            "## 文档列表",
            "",
        ]

        for entry in self.topics:
            lines.append(f"### {entry['title']}")
            lines.append(f"- 文档ID: {entry['document_id']}")
            lines.append(f"- 主题数: {entry['topic_count']}")
            lines.append(f"- 分块数: {entry['chunk_count']}")
            lines.append("")

            if entry["topics"]:
                lines.append("#### 主题")
                for topic in entry["topics"]:
                    lines.append(f"- {topic['section']}")
                lines.append("")

        return "\n".join(lines)

    def generate_skill_markdown(self) -> str:
        """Generate SKILL.md header template."""
        lines = [
            "# 技能定义",
            "",
            "## 概述",
            "- 用途: ",
            "- 适用场景: ",
            "- 评估标准: ",
            "",
            "## 判断逻辑",
            "- 维度1: ",
            "- 维度2: ",
            "- 维度3: ",
            "",
            "## 示例",
            "",
        ]
        return "\n".join(lines)

    def export_json(self, path: Path) -> None:
        """Export index to JSON."""
        data = {
            "topics": self.topics,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def import_json(self, path: Path) -> None:
        """Import index from JSON."""
        data = json.loads(path.read_text())
        self.topics = data.get("topics", [])