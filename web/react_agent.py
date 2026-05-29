"""React Agent — Multi-step psychological analysis with LLM.

Supports two modes:
1. Direct materials: 2-step (extract facts → framework analysis)
2. Agentic RAG: 4-step (explore KB → decide what to read → fetch → analyze)
   The agent autonomously browses the knowledge base, decides which documents
   are relevant, reads only those, then performs the analysis.
"""
from __future__ import annotations

import json
import re
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class ReactAnalyzer:
    """Multi-step React Agent for psychological analysis.

    Two analysis paths:
    - analyze(): Direct materials → 2-step analysis
    - analyze_with_kb(): Agentic RAG → explore KB → decide → fetch → analyze

    All methods accept an optional on_progress(message: str) callback
    for real-time progress reporting.
    """

    def __init__(self):
        self._llm = None
        self._on_progress = None

    @property
    def llm(self):
        if self._llm is None:
            from person_fenxi_core.llm_client import MiniMaxClient
            self._llm = MiniMaxClient()
        return self._llm

    # ==================== Direct Materials Path ====================

    def analyze(self, system_prompt: str, target: str, materials: str,
                output_template: str, theory: str, workflow: str,
                display_name: str = "", on_progress=None) -> str:
        """Run 2-step analysis with directly provided materials.

        Step 1: Extract factual observations
        Step 2: Framework-specific deep analysis
        """
        self._on_progress = on_progress
        fw_label = display_name or "心理分析"

        # === Step 1: Extract factual observations ===
        self._emit("正在从材料中提取关键事实...")
        step1 = self._call(
            system_prompt,
            f"""## 任务：从材料中提取所有关键观察点

## 分析对象
{target}

## 材料
{materials}

## 要求
仔细阅读材料，提取所有可观察的事实和行为，格式：
| 序号 | 场景/情境 | 具体行为/原话 | 来源 |

注意：
- 只提取事实和具体行为，不要做任何推断或评价
- 引用原文关键语句
- 覆盖材料中所有重要段落"""
        )

        # === Step 2: Framework-specific deep analysis ===
        self._emit(f"正在使用「{fw_label}」框架进行深度分析...")
        return self._run_deep_analysis(
            system_prompt=system_prompt,
            target=target,
            facts=step1,
            materials=materials,
            theory=theory or "",
            workflow=workflow or "请按照框架方法论进行深入分析",
            template=output_template or "请输出完整的结构化分析报告。",
            fw_label=fw_label,
        )

    # ==================== Agentic RAG Path ====================

    def analyze_with_kb(self, system_prompt: str, target: str,
                        kb_browser, output_template: str, theory: str,
                        workflow: str, display_name: str = "",
                        on_progress=None) -> str:
        """Agentic RAG: Agent autonomously explores the knowledge base,
        decides what to read, fetches only relevant content, then analyzes.

        Args:
            system_prompt: Role definition from skill
            target: Person being analyzed
            kb_browser: KnowledgeBrowser instance for the selected KB
            output_template: Output format template
            theory: Core theory from skill
            workflow: Analysis workflow from skill
            display_name: Human-readable framework name
            on_progress: Optional callback(message: str) for progress updates

        Returns:
            Complete analysis report
        """
        self._on_progress = on_progress
        fw_label = display_name or "心理分析"

        # === Step 0: Build KB overview for the agent ===
        self._emit("正在浏览知识库结构...")
        kb_overview = self._build_kb_overview(kb_browser)

        # === Step 1: Agent explores KB and decides what to read ===
        self._emit("Agent 正在分析文档相关性，制定阅读计划...")
        plan_text = self._call(
            system_prompt,
            f"""## 任务：浏览知识库，制定阅读计划

## 分析对象
{target}

## 知识库概览
{kb_overview}

## 你的角色
你是一位心理分析师，准备对「{target}」进行深度分析。你面前有一个知识库，
里面包含多篇文档。你需要先浏览知识库的结构，然后决定需要深读哪些内容。

## 要求
请输出一个 JSON 格式的阅读计划（只输出 JSON，不要其他文字）：

```json
{{
    "documents_to_read": ["文档名称1", "文档名称2"],
    "search_queries": ["关键词1", "关键词2"],
    "reasoning": "简述为什么选择这些内容"
}}
```

决策原则：
- 从文档标题和章节判断相关性，选择与「{target}」最相关的文档
- 如果文档标题包含人名且不匹配分析对象，不要选
- search_queries 是额外的关键词搜索，用于查找特定主题（如性格、行为、关系、成长经历等）
- 选择 1-3 篇最相关的文档即可，宁少勿多"""
        )

        # Parse the reading plan (handle both pure JSON and markdown-wrapped JSON)
        plan = self._parse_json_response(plan_text)
        docs_to_read = plan.get("documents_to_read", [])
        search_queries = plan.get("search_queries", [])

        # === Step 2: Fetch only relevant content ===
        if docs_to_read:
            self._emit(f"正在读取选定文档: {', '.join(docs_to_read[:3])}...")
        if search_queries:
            self._emit(f"正在搜索关键词: {', '.join(search_queries[:5])}...")
        materials = self._fetch_relevant_content(kb_browser, plan)
        if not materials:
            # Fallback: if parsing failed, load all documents
            self._emit("正在加载知识库全部文档...")
            materials = self._fallback_load_all(kb_browser)

        self._emit(f"已获取 {len(materials)} 字材料，开始分析...")
        # === Step 3-4: Normal analysis with the fetched materials ===
        return self.analyze(
            system_prompt=system_prompt,
            target=target,
            materials=materials,
            output_template=output_template,
            theory=theory,
            workflow=workflow,
            display_name=display_name,
        )

    # ==================== Internal Helpers ====================

    def _build_kb_overview(self, kb_browser) -> str:
        """Build a structured overview of the knowledge base for the agent."""
        lines = [f"知识库：{kb_browser.kb_name}", ""]

        structure = kb_browser.get_kb_structure()
        docs = structure.get("documents", [])

        if not docs:
            # Try listing documents directly
            doc_names = kb_browser.list_documents()
            if doc_names:
                lines.append("## 文档列表")
                for name in doc_names:
                    lines.append(f"- {name}")
            else:
                lines.append("（知识库为空）")
            return "\n".join(lines)

        lines.append("## 文档概览")
        lines.append("")

        for doc in docs:
            doc_id = doc.get("doc_id", "未知")
            chunk_count = doc.get("chunk_count", 0)
            sections = doc.get("sections", [])

            lines.append(f"### {doc_id}")
            lines.append(f"- 内容块数：{chunk_count}")
            if sections:
                lines.append(f"- 章节主题：{' · '.join(sections[:8])}")
            lines.append("")

        return "\n".join(lines)

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from ```json ... ``` block
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find raw JSON object
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {"documents_to_read": [], "search_queries": [], "reasoning": "无法解析"}

        try:
            plan = json.loads(json_str)
            return {
                "documents_to_read": plan.get("documents_to_read", []),
                "search_queries": plan.get("search_queries", []),
                "reasoning": plan.get("reasoning", ""),
            }
        except json.JSONDecodeError:
            return {"documents_to_read": [], "search_queries": [], "reasoning": "JSON解析失败"}

    def _fetch_relevant_content(self, kb_browser, plan: dict) -> str:
        """Fetch only the content the agent decided to read."""
        parts = []

        docs_to_read = plan.get("documents_to_read", [])
        search_queries = plan.get("search_queries", [])

        # Read specified documents
        for doc_id in docs_to_read:
            doc = kb_browser.read_document(doc_id)
            if doc:
                parts.append(f"# {doc.title}\n\n{doc.content}")
            else:
                # Try by name
                content = kb_browser.read_document_by_name(doc_id)
                if content:
                    parts.append(f"# {doc_id}\n\n{content}")

        # Execute search queries
        for query in search_queries:
            result = kb_browser.search_by_keyword(query, max_docs=3)
            for doc in result.documents:
                parts.append(f"# [搜索: {query}] {doc.doc_id}\n\n{doc.content}")

        return "\n\n---\n\n".join(parts) if parts else ""

    def _fallback_load_all(self, kb_browser) -> str:
        """Fallback: load all documents if parsing failed."""
        doc_names = kb_browser.list_documents()
        if not doc_names:
            return ""

        all_content = []
        for doc_id in doc_names:
            doc = kb_browser.read_document(doc_id)
            if doc:
                all_content.append(f"# {doc.title}\n\n{doc.content}")

        return "\n\n---\n\n".join(all_content)

    def _run_deep_analysis(self, system_prompt: str, target: str, facts: str,
                           materials: str, theory: str, workflow: str,
                           template: str, fw_label: str) -> str:
        """Run the framework-specific deep analysis."""
        return self._call(
            system_prompt,
            f"""## 任务：使用【{fw_label}】框架进行完整深度分析

## 分析对象
{target}

## 从材料中提取的事实
{facts}

## 原始材料（供对照）
{materials}

## 框架理论知识
{theory}

## 分析步骤（必须严格执行）
{workflow}

## 输出格式（必须严格遵循）
{template}

## 重要提醒
1. 每一步都不能跳过
2. 每个判断都要有从原始材料中提取的证据链
3. 分析要深入具体，不能泛泛而谈
4. 严格按照输出格式的章节结构组织报告"""
        )

    def _call(self, system_prompt: str, user_content: str) -> str:
        """Single LLM call with generous token limit for full analysis reports."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        try:
            self._emit("正在调用大模型进行分析...")
            response = self.llm.chat_completion(messages, max_tokens=8192, timeout=600.0)
            return response.content
        except Exception as e:
            return f"[错误: {e}]"

    def _emit(self, message: str) -> None:
        """Emit progress update if callback is set."""
        if self._on_progress:
            self._on_progress(message)
