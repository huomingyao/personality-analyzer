"""React Agent — Multi-step psychological analysis with LLM.

Instead of a single LLM call, this agent executes the SKILL.md workflow
step-by-step, accumulating context and producing deep analysis.
"""
from __future__ import annotations

import sys
import os

PROJECT_DIR = r"D:\person_fenxi"
SRC_DIR = os.path.join(PROJECT_DIR, "src")
for p in [SRC_DIR, PROJECT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)


class ReactAnalyzer:
    """Multi-step React Agent for psychological analysis.

    Executes a skill's analysis workflow in separate LLM calls:
    1. Extract behaviors from materials
    2. Ask motivation for each behavior, map to framework colors
    3. Statistics + pattern matching + cross-source validation
    4. Produce final report following the output template
    """

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from llm_client import MiniMaxClient
            self._llm = MiniMaxClient()
        return self._llm

    def analyze(self, system_prompt: str, target: str, materials: str,
                output_template: str, theory: str, workflow: str) -> str:
        """Run multi-step React analysis.

        Args:
            system_prompt: Role definition from skill
            target: Person being analyzed
            materials: Source materials
            output_template: Output format template
            theory: Core theory (behavior lookup, diagnostic rules)
            workflow: Step-by-step analysis workflow

        Returns:
            Complete analysis report
        """
        ctx = {
            "target": target,
            "materials": materials,
            "theory": theory,
            "template": output_template,
        }

        # === Step 1: Extract behaviors ===
        step1 = self._call(
            system_prompt,
            f"""## 任务：从材料中提取所有关键行为

## 分析对象
{target}

## 材料
{materials}

## 要求
从材料中提取每一个可观察的行为，格式：
| 序号 | 情境/场景 | 具体行为 | 结果/后果 | 来源 |
|------|-----------|----------|-----------|------|

注意：
- 只提取具体行为，不要做任何推断或评价
- 引用原文关键语句
- 每个行为一行"""
        )
        ctx["behaviors"] = step1

        # === Step 2: Motivate + Map ===
        step2 = self._call(
            system_prompt,
            f"""## 任务：对每一个行为追问动机，映射到色彩

## 已提取的行为
{step1}

## 核心理论
{theory}

## 要求
对上述每个行为，追问"TA为什么这样做？"，推断深层动机，然后映射到四色之一。

格式：
| 序号 | 行为摘要 | 追问"为什么" | 推断动机 | 对应色彩 | 置信度 |
|------|----------|--------------|----------|----------|--------|

关键：
- 相同行为可能来自不同动机，必须穿透行为看动机
- 动机映射：快乐→红色、完美→蓝色、控制→黄色、稳定→绿色
- 每个动机必须有推理链条，不能直接贴标签"""
        )
        ctx["motivations"] = step2

        # === Step 3: Statistics + Cross-source validation ===
        step3 = self._call(
            system_prompt,
            f"""## 任务：统计动机分布 + 多来源验证 + 不共存检验

## 动机分析结果
{step2}

## 材料原文
{materials}

## 诊断铁律
- 强红+强蓝：必有后天修饰（红蓝不共存）
- 强黄+强绿：必有后天修饰（黄绿不共存）

## 要求

### 3.1 多来源验证表
| 行为/动机 | 出现次数 | 可信度 | 来源文件 |
|-----------|---------|--------|---------|

### 3.2 动机强度统计
| 动机 | 出现次数 | 占比 |
|------|---------|------|
| 快乐（红） | X | X% |
| 完美（蓝） | X | X% |
| 控制（黄） | X | X% |
| 稳定（绿） | X | X% |

### 3.3 不共存检验
检查是否存在红蓝或黄绿同时强的情况，如果存在，判断哪个是后天修饰。

### 3.4 先天/后天分离
- 先天性格（跨情境一致、反复出现）：
- 后天个性（特定环境、特定角色）："""
        )
        ctx["stats"] = step3

        # === Step 4: Final report ===
        final = self._call(
            system_prompt,
            f"""## 任务：按照模板生成最终分析报告

## 所有分析结果
### 行为提取
{step1}

### 动机分析
{step2}

### 统计验证
{step3}

## 输出模板（必须严格遵循）
{output_template}

## 分析对象：{target}

## 重要
1. 必须严格按照输出模板的章节结构
2. 每个判断都要有证据链支撑
3. 分析要深入、具体，不能泛泛而谈
4. 用上面每一步的分析结果来填充模板"""
        )

        return final

    def _call(self, system_prompt: str, user_content: str) -> str:
        """Single LLM call."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        try:
            response = self.llm.chat_completion(messages)
            return response.content
        except Exception as e:
            return f"[错误: {e}]"
