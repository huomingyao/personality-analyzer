"""Critic review service - HCT quality gatekeeper for analysis results."""
from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import Knowledge Browser
from kb_browser import KnowledgeBrowser, create_browser


@dataclass
class ReviewResult:
    """Result of a critic review."""

    passed: bool
    decision: str  # "PASS" | "REVISE" | "REJECT"
    score: int  # 0-100
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)  # Socratic probes
    suggestions: list[str] = field(default_factory=list)
    revision_notes: str = ""  # What to fix for next iteration
    raw_report: str = ""


class CriticService:
    """HCT quality gatekeeper for psychological analysis."""

    def __init__(self):
        self._llm = None
        self._browser: KnowledgeBrowser | None = None

    @property
    def llm(self):
        if self._llm is None:
            from person_fenxi_core.llm_client import MiniMaxClient
            self._llm = MiniMaxClient()
        return self._llm

    @property
    def browser(self) -> KnowledgeBrowser:
        if self._browser is None:
            self._browser = KnowledgeBrowser()
        return self._browser

    # ==================== 知识库浏览（Critic 主动获取参考） ====================

    def set_knowledge_base(self, kb_name: str) -> None:
        """Critic 设置使用的知识库"""
        self._browser = KnowledgeBrowser(kb_name)

    def search_knowledge_for_review(self, query: str) -> str:
        """Critic 主动搜索知识库，用于验证分析结论

        Args:
            query: 搜索关键词，可以是分析中的关键判断

        Returns:
            知识库中匹配的内容，用于验证分析质量
        """
        result = self.browser.search_by_keyword(query, max_docs=3)

        if not result.documents:
            return ""

        contents = []
        for doc in result.documents[:3]:  # 限制数量
            excerpt = doc.content[:1500]  # 截取片段
            contents.append(f"### 参考: {doc.doc_id}")
            contents.append(excerpt)

        return "\n".join(contents)

    def browse_document_for_critique(self, doc_id: str) -> str:
        """Critic 读取指定文档用于对照审查"""
        doc = self.browser.read_document(doc_id)
        if not doc:
            return self.browser.read_document_by_name(doc_id)
        return doc.content

    def verify_conclusion(self, analysis: str, verification_target: str = "") -> str:
        """Critic 验证分析结论是否与原始材料一致

        Args:
            analysis: 分析报告
            verification_target: 想要验证的关键词

        Returns:
            从知识库中找到的相关内容，用于判断分析是否准确
        """
        if not verification_target:
            # 从分析中提取关键概念验证
            keywords = self._extract_keywords(analysis)
            if keywords:
                verification_target = keywords[0]

        if verification_target:
            return self.search_knowledge_for_review(verification_target)

        return ""

    def _extract_keywords(self, text: str) -> list[str]:
        """从文本中提取关键词（简单实现）"""
        import re
        # 提取引号中的词和专业术语
        patterns = [
            r'"([^"]+)"',  # 引号内容
            r'「([^」]+)」',  # 中文引号
            r'是（一[个种些]|某种）([^的，。,\n]+)',  # "是X"的模式
        ]

        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend([m[1] if isinstance(m, tuple) else m for m in matches])

        return keywords[:5]

    # === Fast syntactic checks ===

    def quick_check(self, analysis_text: str, framework_id: str | None = None) -> list[str]:
        """Fast structural validation without LLM call. Returns list of issues."""
        issues = []

        # Check 1: too short = insufficient depth
        if len(analysis_text) < 500:
            issues.append("分析文太短（<500字），可能分析深度不够")

        # Check 2: must contain target identity
        if "分析报告" not in analysis_text and "分析：" not in analysis_text and "报告：" not in analysis_text:
            issues.append("缺少分析报告标题或分析对象标识")

        # Check 3: framework-specific checks
        if framework_id == "性格色彩分析":
            must_have = ["色彩判定", "先天性格", "动机"]
            for kw in must_have:
                if kw not in analysis_text:
                    issues.append(f"性格色彩分析缺少关键模块：「{kw}」")

        return issues

    # === Deep LLM-based review ===

    def review(self, target: str, materials: str, analysis: str,
               framework_id: str | None = None, max_iterations: int = 3,
               kb_name: str = "", verify_conclusions: bool = False) -> ReviewResult:
        """Full HCT review of an analysis result.

        Args:
            target: 被分析对象
            materials: 原始材料（或从知识库获取）
            analysis: 待审查的分析报告
            framework_id: 分析框架
            max_iterations: 最大迭代次数
            kb_name: 知识库名称（让 Critic 可以主动查阅）
            verify_conclusions: 是否从知识库验证分析结论

        当提供 kb_name 时，Critic 可以主动搜索知识库来验证分析结论。
        """
        # 新增：支持知识库验证模式
        verification_content = ""
        if kb_name:
            self.set_knowledge_base(kb_name)
            if verify_conclusions:
                verification_content = self.verify_conclusion(analysis)
        # Phase 1: quick structural check
        quick_issues = self.quick_check(analysis, framework_id)
        if len(quick_issues) >= 3:
            return ReviewResult(
                passed=False,
                decision="REJECT",
                score=0,
                weaknesses=quick_issues,
                revision_notes="\n".join(quick_issues),
            )

        # Phase 2: deep LLM-based review
        review_prompt = self._build_review_prompt(target, materials, analysis, framework_id)
        messages = [
            {"role": "system", "content": self._review_system_prompt()},
            {"role": "user", "content": review_prompt},
        ]

        try:
            response = self.llm.chat_completion(messages, max_tokens=4096)
            raw = response.content
        except Exception as e:
            return ReviewResult(
                passed=False, decision="REJECT", score=0,
                weaknesses=[f"审查出错: {str(e)}"],
                revision_notes=str(e),
            )

        # Phase 3: parse structured result
        return self._parse_review_result(raw)

    def review_loop(self, target: str, materials: str,
                    analyze_fn, framework_id: str | None = None,
                    max_rounds: int = 3) -> tuple[str, list[ReviewResult]]:
        """Full review loop: analyze → review → revise → ... → pass or max rounds.

        Args:
            target: analysis target
            materials: source materials
            analyze_fn: callable that takes (target, materials, revision_notes) -> new_analysis_text
            framework_id: which framework
            max_rounds: max iterations

        Returns:
            (final_analysis, review_history)
        """
        history: list[ReviewResult] = []
        revision_notes = ""
        final_analysis = ""

        for round_num in range(1, max_rounds + 1):
            # Analyze (with revision notes from previous failure)
            final_analysis = analyze_fn(target, materials, revision_notes) if revision_notes else analyze_fn(target, materials, "")

            # Review
            result = self.review(target, materials, final_analysis, framework_id)
            history.append(result)

            if result.passed:
                break

            revision_notes = result.revision_notes
            if not revision_notes:
                revision_notes = "\n".join(result.weaknesses)

        return final_analysis, history

    # === Internal helpers ===

    def _review_system_prompt(self) -> str:
        return """你是一个严格的心理分析质量审查员（HCT批判思维框架）。

你的任务是审查一份心理分析报告的**质量**，而不是审查被分析者本人。

审查标准：
1. 分析是否深入？是否穿透行为表象到达深层动机？
2. 逻辑是否自洽？结论是否有充分证据支持？
3. 有没有考虑其他可能解释（反例）？
4. 分析结构是否完整？是否符合框架要求？
5. 有没有自我矛盾的地方？
6. 判断是否有"贴标签"倾向？是否区分了先天vs后天？

你需要输出严格的结构化审查结果。"""

    def _build_review_prompt(self, target: str, materials: str, analysis: str,
                             framework_id: str | None = None,
                             verification_content: str = "") -> str:
        fw_label = f"（使用框架：{framework_id}）" if framework_id else ""

        # 添加知识库验证内容（如果有）
        verify_section = ""
        if verification_content:
            verify_section = f"""
## 知识库参考资料（用于验证分析结论）
{verification_content}
"""

        return f"""请严格审查以下心理分析报告的质量{fw_label}。

## 被分析对象
{target}

## 原始材料
{materials[:2000] if materials else "[从知识库获取]"}

## 待审查的分析报告
{analysis}
{verify_section}

## 审查要求

请按以下格式输出（必须严格遵循格式）：

### 评分
[0-100分]

### 判定
[PASS / REVISE / REJECT]
- PASS: 分析质量达标，可以输出
- REVISE: 有改进空间，需要修改后重新提交
- REJECT: 质量严重不合格，需要从头重做

### 优点
- [列出分析的优点]

### 问题
- [列出分析存在的问题，每条一行]
- [严重问题标为 🔴，中等问题标为 🟡]

### 索卡尔追问
- [对关键判断提出追问]
- [例如："这个结论的证据在哪里？"]
- [例如："有没有可能是其他原因导致的？"]

### 修改建议（仅当判定为 REVISE 时）
- [具体的修改方向]"""

    def _parse_review_result(self, raw: str) -> ReviewResult:
        """Parse LLM review output into structured result."""
        import re

        # Extract score
        score_match = re.search(r"评分[：:]\s*(\d+)", raw)
        score = min(100, max(0, int(score_match.group(1)) if score_match else 50))

        # Extract decision
        decision = "REVISE"
        if "PASS" in raw.upper() and "REVISE" not in raw.upper():
            decision = "PASS"
        elif "REJECT" in raw.upper():
            decision = "REJECT"

        # Threshold-based override
        if score >= 75:
            decision = "PASS"
        elif score < 40:
            decision = "REJECT"

        # Extract strengths (lines after 优点 and before 问题)
        strengths: list[str] = []
        weaknesses: list[str] = []
        questions: list[str] = []
        suggestions: list[str] = []

        current_section = ""
        for line in raw.split("\n"):
            stripped = line.strip()
            if "优点" in stripped and "###" in stripped:
                current_section = "strengths"
                continue
            elif "问题" in stripped and "###" in stripped:
                current_section = "weaknesses"
                continue
            elif "追问" in stripped and "###" in stripped:
                current_section = "questions"
                continue
            elif "建议" in stripped and "###" in stripped:
                current_section = "suggestions"
                continue
            elif stripped.startswith("###"):
                current_section = ""
                continue

            if current_section == "strengths" and stripped.startswith("-"):
                strengths.append(stripped.lstrip("- "))
            elif current_section == "weaknesses" and stripped.startswith("-"):
                weaknesses.append(stripped.lstrip("- "))
            elif current_section == "questions" and stripped.startswith("-"):
                questions.append(stripped.lstrip("- "))
            elif current_section == "suggestions" and stripped.startswith("-"):
                suggestions.append(stripped.lstrip("- "))

        return ReviewResult(
            passed=(decision == "PASS"),
            decision=decision,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            questions=questions,
            suggestions=suggestions,
            revision_notes="\n".join(weaknesses + suggestions),
            raw_report=raw,
        )
