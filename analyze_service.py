"""Services for Psyche KB Web API."""

from __future__ import annotations

import sys
import os
from typing import List, Dict, Any

# Path setup - import from psycle-kb project
PROJECT_DIR = r"D:\person_fenxi"
SRC_DIR = os.path.join(PROJECT_DIR, "src")

for p in [SRC_DIR, PROJECT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)


# Import from parent project
from unified_skill_manager import UnifiedSkillManager, create_unified_manager
from llm_client import MiniMaxClient
from react_agent import ReactAnalyzer

# Import knowledge browser
from kb_browser import KnowledgeBrowser, create_browser, search_kb

# Import new multi-framework orchestrator
import sys
sys.path.insert(0, SRC_DIR)
from multi_framework_orchestrator import create_orchestrator, MultiFrameworkOrchestrator


class AnalyzeService:
    """Service for psychological analysis operations."""

    def __init__(self):
        self._manager: UnifiedSkillManager | None = None
        self._llm: MiniMaxClient | None = None
        self._react: ReactAnalyzer | None = None
        self._browser: KnowledgeBrowser | None = None

    @property
    def browser(self) -> KnowledgeBrowser:
        if self._browser is None:
            self._browser = KnowledgeBrowser()
        return self._browser

    @property
    def manager(self) -> UnifiedSkillManager:
        if self._manager is None:
            self._manager = create_unified_manager()
        return self._manager

    @property
    def llm(self) -> MiniMaxClient:
        if self._llm is None:
            self._llm = MiniMaxClient()
        return self._llm

    @property
    def react(self) -> ReactAnalyzer:
        if self._react is None:
            self._react = ReactAnalyzer()
        return self._react

    def get_available_skills(self) -> List[Dict[str, Any]]:
        """Get list of available analysis frameworks."""
        available = self.manager.find_available_frameworks()
        return available

    # ==================== 知识库浏览（Agent 主动获取材料） ====================

    def set_knowledge_base(self, kb_name: str) -> None:
        """设置当前使用的知识库"""
        self._browser = KnowledgeBrowser(kb_name)

    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有可用知识库"""
        return self.browser.list_knowledge_bases()

    def list_documents(self) -> List[str]:
        """列出现在用的知识库中的文档"""
        return self.browser.list_documents()

    def get_kb_structure(self) -> Dict[str, Any]:
        """获取知识库结构摘要"""
        return self.browser.get_kb_structure()

    def search_knowledge_base(self, query: str) -> str:
        """搜索知识库获取相关内容（Agent 主动搜索）

        Args:
            query: 搜索关键词，如"性格特点"、"情感模式"等

        Returns:
            匹配的知识库内容，多篇文档用分隔
        """
        result = self.browser.search_by_keyword(query, max_docs=5)

        if not result.documents:
            return ""

        # 整理输出
        contents = []
        for doc in result.documents:
            contents.append(f"## {doc.doc_id}")
            if doc.sections:
                contents.append(f"章节: {', '.join(doc.sections)}")
            contents.append(doc.content)
            contents.append("---\n")

        return "\n".join(contents)

    def browse_document(self, doc_id: str) -> str:
        """浏览知识库中的指定文档"""
        doc = self.browser.read_document(doc_id)
        if not doc:
            # 尝试按文件名读取
            return self.browser.read_document_by_name(doc_id)
        return doc.content

    def auto_load_materials_from_kb(self, target: str, material_hint: str = "") -> str:
        """根据分析目标自动从知识库加载相关材料

        这是 Agent 的核心方法：让它可以主动搜索知识库获取分析材料。

        Args:
            target: 分析对象（用于生成搜索关键词）
            material_hint: 材料提示，如"聊天记录"、"日记"、"书信"等

        Returns:
            从知识库获取的材料内容
        """
        # 确定知识库名称
        kb_name = None
        # 从 hint 推断知识库名
        if "聊天" in material_hint or "微信" in material_hint or "对话" in material_hint:
            kb_name = "小明的聊天记录"
        elif "日记" in material_hint:
            kb_name = "测试知识库"
        elif "书" in material_hint:
            kb_name = "心理学的书"

        if kb_name:
            self._browser = KnowledgeBrowser(kb_name)

        # 搜索相关材料
        queries = []

        # 从目标中提取关键词
        if target:
            queries.append(target)

        # 加入 hint
        if material_hint:
            queries.append(material_hint)

        # 通用搜索词
        queries.extend(["性格", "情感", "人际", "成长", "经历"])

        # 去重
        queries = list(set(queries))

        results = self.browser.search_all_keywords(queries[:5], max_per_query=2)

        # 合并结果
        contents = []
        for query, result in results.items():
            if result.documents:
                contents.append(f"### 搜索词: {query}")
                for doc in result.documents:
                    if doc.content:
                        excerpt = doc.content[:2000]  # 限制长度
                        contents.append(f"#### 来源: {doc.doc_id}")
                        contents.append(excerpt)
                        contents.append("")

        if contents:
            return "\n".join(contents)
        else:
            # 没有找到，返回空并给出知识库信息
            return ""

    def analyze(self, target, materials, framework=None,
             kb_name: str = "", kb_search: str = ""):
        """Perform single-framework analysis using React Agent (multi-step).

        Args:
            target: 分析对象
            materials: 直接提供的材料（旧方式）
            framework: 分析框架 ID
            kb_name: 知识库名称（新方式）
            kb_search: 知识库搜索词，让 Agent 可以主动搜索知识库

        当提供 kb_name 时，Agent 会主动搜索知识库获取材料，不再依赖 materials 参数。
        """
        # 新增：支持知识库搜索模式
        if kb_name:
            self.set_knowledge_base(kb_name)
            # Agent 主动搜索知识库
            if kb_search:
                materials = self.search_knowledge_base(kb_search)
            else:
                # 没有搜索词，列出结构让 Agent 选择
                structure = self.get_kb_structure()
                # 空材料，后续由 Agent 自己决定如何读取
                materials = f"[知识库: {kb_name}]\n" \
                          f"文档列表: {structure.get('documents', [])}"

        fw_id = framework or "liangebodwo-mirror"

        # Gather skill components for the React agent
        system_prompt = self.manager.get_system_prompt(fw_id)
        content = ""
        if self.manager.frameworks.get(fw_id) and self.manager.frameworks[fw_id].loaded_skill:
            content = self.manager.frameworks[fw_id].loaded_skill.content

        template = self.manager._extract_output_template(content)
        workflow = self.manager._extract_section(content, "分析流程")
        if not workflow:
            # Fallback: use description + first part of prompt_template
            workflow = self.manager.frameworks[fw_id].description if fw_id in self.manager.frameworks else ""

        # Use prompt_template as theory (trimmed)
        theory = ""
        if fw_id in self.manager.frameworks and self.manager.frameworks[fw_id].prompt_template:
            theory = self.manager.frameworks[fw_id].prompt_template[:3000]

        # Run React agent (4-step loop)
        return self.react.analyze(
            system_prompt=system_prompt,
            target=target,
            materials=materials,
            output_template=template,
            theory=theory,
            workflow=workflow,
        )

    def analyze_multi(self, target, materials, frameworks):
        """Perform multi-framework analysis with independent reports and cross-framework detection.

        Each framework analyzes independently, then a critic detects contradictions
        between frameworks. If contradictions are found, the affected frameworks
        are asked to re-examine their conclusions.
        """
        # Use the new MultiFrameworkOrchestrator for independent analysis
        orchestrator = create_orchestrator(self.manager, self.llm)

        result = orchestrator.run_parallel_analysis(
            target=target,
            materials=materials,
            framework_ids=frameworks,
            max_iterations=2,
        )

        # Format as independent reports (not merged)
        return orchestrator.format_independent_reports(result)

    def analyze_with_prompt(self, prompt: str, framework_id: str = "liangebodwo-mirror") -> str:
        """Perform analysis with a raw prompt (used for Critic revision)."""
        system_prompt = self.manager.get_system_prompt(framework_id)
        revision_note = "请根据Critic的反馈重新分析，提高分析深度和准确性。"

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{revision_note}"},
            {"role": "user", "content": prompt},
        ]
        try:
            response = self.llm.chat_completion(messages)
            return response.content
        except Exception as e:
            return f"分析出错: {str(e)}"

    def build_revision_prompt(self, framework_id: str, target: str,
                              materials: str, revision_notes: str) -> str:
        """Build a re-analysis prompt with Critic feedback included."""
        fw = self.manager.frameworks.get(framework_id)
        if not fw or not fw.enabled:
            return f"""# 重新分析请求

## 分析对象
{target}

## 材料
{materials}

## 上次分析的不足之处（请针对性改进）
{revision_notes}

请重新进行分析，特别针对以上不足进行改进。"""

        return f"""# 重新分析请求（经Critic审查后修订）

## 分析框架
{fw.display_name}
{fw.description}

## 分析对象
{target}

## 材料
{materials}

## Critic反馈（必须针对性改进）
{revision_notes}

{fw.prompt_template}

请重新进行完整分析，特别注意针对Critic反馈中的问题进行改进。
分析必须更深入、更有证据支撑、逻辑更自洽。"""