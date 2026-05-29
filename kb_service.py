"""知识库服务 — Corpus2Skill 流水线集成"""

from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Any

# 引入已有的 corpus2skill 流水线
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from corpus2skill.chunker import TextChunker, ChunkConfig
from corpus2skill.indexer import SkillIndexer
from corpus2skill.navigator import KnowledgeNavigator
from models import Chunk, Document, DocumentType


KB_BASE = Path(r"D:\person_fenxi\web_api\knowledge_bases")


def _read_file(file_path: str) -> str:
    """Read file content, auto-detecting format."""
    content = extract_text(Path(file_path))
    if not content:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            content = '[无法解析的文件]'
    return content


# ==================== 文件读取 ====================

def extract_text(file_path: Path) -> str:
    """Extract text from any supported format."""
    ext = file_path.suffix.lower()
    try:
        if ext == '.docx':
            from docx import Document as DocxDoc
            doc = DocxDoc(str(file_path))
            return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == '.pdf':
            import fitz
            text = []
            with fitz.open(str(file_path)) as doc:
                for page in doc:
                    text.append(page.get_text())
            return '\n'.join(text)
        else:
            for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    return file_path.read_text(encoding=enc)
                except UnicodeDecodeError:
                    continue
            return file_path.read_bytes().decode('utf-8', errors='ignore')
    except Exception:
        return ''


# ==================== Corpus2Skill 流水线 ====================

def process_document(file_path: Path, kb_name: str) -> dict[str, Any]:
    """Run the full Corpus2Skill pipeline on a single document.

    Flow: 读取 → 分块 → 索引 → 生成 INDEX.md
    """
    doc_id = file_path.stem
    content = extract_text(file_path)
    if not content:
        return {"error": "无法提取文本内容"}

    # Step 1: 分块
    chunker = TextChunker(ChunkConfig(max_chunk_size=800, min_chunk_size=100, overlap=50))
    chunks = chunker.chunk_document(doc_id, content, title=doc_id)

    # Step 2: 构建 Document + 索引
    doc = Document(
        id=doc_id,
        title=doc_id,
        content=content,
        doc_type=DocumentType.CORPUS,
        file_path=file_path,
    )
    indexer = SkillIndexer()
    indexer.index_document(doc, chunks)

    # Step 3: 生成 INDEX.md
    index_md = indexer.generate_skill_index()

    # Step 4: 持久化 chunks 和 index
    kb_dir = KB_BASE / kb_name
    pipeline_dir = kb_dir / ".pipeline"
    pipeline_dir.mkdir(exist_ok=True)

    # 保存 chunks
    chunks_data = [
        {
            "id": c.id,
            "content": c.content,
            "section_title": c.metadata.get("section_title", ""),
            "chunk_index": c.chunk_index,
        }
        for c in chunks
    ]
    (pipeline_dir / f"{doc_id}_chunks.json").write_text(
        json.dumps(chunks_data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    # 保存 index
    (pipeline_dir / f"{doc_id}_index.md").write_text(index_md, encoding='utf-8')

    # 更新知识库总索引
    update_kb_index(kb_name)

    return {
        "doc_id": doc_id,
        "chunk_count": len(chunks),
        "index_md": index_md,
        "chunks": chunks_data,
    }


def update_kb_index(kb_name: str) -> dict[str, Any]:
    """Rebuild the knowledge base master index."""
    kb_dir = KB_BASE / kb_name
    pipeline_dir = kb_dir / ".pipeline"
    if not pipeline_dir.exists():
        return {"error": "暂无索引"}

    # 收集所有文档的 chunks JSON
    all_entries = []
    for f in sorted(pipeline_dir.glob("*_chunks.json")):
        data = json.loads(f.read_text(encoding='utf-8'))
        doc_id = f.stem.replace("_chunks", "")
        sections = list(set(c.get("section_title", "") for c in data if c.get("section_title")))
        all_entries.append({
            "doc_id": doc_id,
            "chunk_count": len(data),
            "sections": sections,
        })

    # 生成总 INDEX.md
    lines = [
        f"# 📚 {kb_name} · 知识索引",
        "",
        f"> 自动生成 | {time.strftime('%Y-%m-%d %H:%M')} | {len(all_entries)} 篇文档",
        "",
        "---",
        "",
        "## 文档索引",
        "",
    ]

    for entry in all_entries:
        lines.append(f"### 📄 {entry['doc_id']}")
        lines.append(f"- 分块数: {entry['chunk_count']}")
        if entry['sections']:
            lines.append(f"- 主题: {' · '.join(entry['sections'][:10])}")
        lines.append("")

    index_md = "\n".join(lines)
    (pipeline_dir / "INDEX.md").write_text(index_md, encoding='utf-8')

    return {"entries": all_entries, "index_md": index_md}


def get_kb_tree(kb_name: str) -> dict[str, Any]:
    """Get the knowledge tree for a knowledge base."""
    kb_dir = KB_BASE / kb_name
    pipeline_dir = kb_dir / ".pipeline"

    if not pipeline_dir.exists():
        return {"kb_name": kb_name, "documents": [], "index_md": ""}

    # 读取总索引
    index_path = pipeline_dir / "INDEX.md"
    index_md = index_path.read_text(encoding='utf-8') if index_path.exists() else ""

    # 读取每个文档的 chunks
    documents = []
    for f in sorted(pipeline_dir.glob("*_chunks.json")):
        doc_id = f.stem.replace("_chunks", "")
        data = json.loads(f.read_text(encoding='utf-8'))
        documents.append({
            "doc_id": doc_id,
            "chunk_count": len(data),
            "sections": list(set(c.get("section_title", "") for c in data if c.get("section_title"))),
            "chunks": data,  # 完整 chunks 内容
        })

    return {
        "kb_name": kb_name,
        "documents": documents,
        "index_md": index_md,
    }


def get_document_chunks(kb_name: str, doc_id: str) -> list[dict]:
    """Get chunks for a specific document."""
    pipeline_dir = KB_BASE / kb_name / ".pipeline"
    chunks_file = pipeline_dir / f"{doc_id}_chunks.json"
    if not chunks_file.exists():
        return []
    return json.loads(chunks_file.read_text(encoding='utf-8'))
