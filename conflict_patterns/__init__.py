"""Conflict pattern definitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConflictPattern:
    """A conflict pattern between two color types."""

    name: str                 # Pattern name, e.g., "blue_logic_pressure"
    trigger_color: str         # Speaker's color type
    trigger_patterns: list[str]  # Keywords/triggers that activate this pattern

    feel_when_triggered: str    # How the other side feels
    risk_level: str           # "high" | "medium" | "low"

    counter_suggestions: list[str] = None  # How to respond appropriately

    def __post_init__(self) -> None:
        if self.counter_suggestions is None:
            self.counter_suggestions = []


# Core conflict patterns between four colors
CONFLICT_PATTERNS: list[ConflictPattern] = [
    # ========== Blue triggers Red ==========
    ConflictPattern(
        name="blue_logic_pressure",
        trigger_color="蓝色",
        trigger_patterns=[
            "逻辑", "道理", "理性", "论证", "证据", "事实",
            "这个问题", "本质是", "原因", "所以", "因此",
            "你应该", "你必须", "你这样不对", "你理解错了",
            "我证明了", "数据显示", "研究显示",
        ],
        feel_when_triggered="被否定、不被理解、没有被看见",
        risk_level="high",
        counter_suggestions=[
            "先回应情绪，再回应事情",
            "问「你现在是什么感受」而非「你是怎么想的」",
            "红色需要情感连接，先安抚再讲理"
        ],
    ),

    ConflictPattern(
        name="blue_perfectionism",
        trigger_color="蓝色",
        trigger_patterns=[
            "不对", "错了", "不行", "这样不好",
            "你有漏洞", "你考虑不全", "还有问题",
            "细节", "精确", "准确", "严谨",
        ],
        feel_when_triggered="被挑剔、无论怎么做都不对",
        risk_level="medium",
        counter_suggestions=[
            "肯定对方的仔细",
            "区分「事情」和「人」"
        ],
    ),

    # ========== Red triggers Blue ==========
    ConflictPattern(
        name="red_emotional_dumping",
        trigger_color="红色",
        trigger_patterns=[
            "我难过", "我郁闷", "我烦", "我气的",
            "你知道吗", "真的太xxx", "气死了",
            "哭", "委屈", "伤心", "难受",
            "不管了", "烦死了", "累死了",
        ],
        feel_when_triggered="被情感淹没、不知如何回应",
        risk_level="high",
        counter_suggestions=[
            "先倾听陪伴",
            "给红色表达的空间",
            "黄色需要行动，先问「我能帮你做什么」"
        ],
    ),

    ConflictPattern(
        name="red_dramatic_reaction",
        trigger_color="红色",
        trigger_patterns=[
            "完了", "没救了", "死定了",
            "再也不", "永远不要", "受够了",
            "太夸张", "没那么严重",
        ],
        feel_when_triggered="被情绪卷入、感到失控",
        risk_level="medium",
        counter_suggestions=[
            "帮助红色冷静下来",
            "问「现在情况真的那么糟吗」"
        ],
    ),

    # ========== Yellow triggers Green ==========
    ConflictPattern(
        name="yellow_impatience",
        trigger_color="黄色",
        trigger_patterns=[
            "快点", "赶紧", "赶快", "动作快",
            "怎么还没", "怎么那么慢",
            "效率", "速度", "行动",
            "我在等", "你已经xxx了",
            "还等什么", "上啊",
        ],
        feel_when_triggered="被催促、压力好大、喘不过气",
        risk_level="medium",
        counter_suggestions=[
            "给绿色准备时间",
            "用「我们什么时候开始」而非「现在马上」"
        ],
    ),

    ConflictPattern(
        name="yellow_demanding",
        trigger_color="黄色",
        trigger_patterns=[
            "你要做到", "你必须完成", "搞定",
            "别说了", "做就行了",
            "结果导向", "只看结果",
        ],
        feel_when_triggered="被控制、没有选择",
        risk_level="medium",
        counter_suggestions=[
            "给绿色表达意见的机会"
        ],
    ),

    # ========== Green triggers Yellow ==========
    ConflictPattern(
        name="green_passivity",
        trigger_color="绿色",
        trigger_patterns=[
            "都可以", "随便", "无所谓",
            "你决定", "我都行", "听你的",
            "再等等", "看看吧", "再说吧",
            "不急", "慢慢来",
        ],
        feel_when_triggered="皇帝不急太监急、无法推动",
        risk_level="low",
        counter_suggestions=[
            ".yellow_gives_deadline",
            "明确给黄颜色一个截止时间",
            "主动推动而非等待"
        ],
    ),

    ConflictPattern(
        name="green_avoidance",
        trigger_color="绿色",
        trigger_patterns=[
            "下次吧", "以后再说", "到时候",
            "我不知道", "我没想法",
            "逃避", "躲",
        ],
        feel_when_triggered="被拖延、有力无处使",
        risk_level="medium",
        counter_suggestions=[
            "把问题拆解成小步骤"
        ],
    ),

    # ========== Color-specific responses ==========
    # When RED receives logic pressure (from BLUE)
    ConflictPattern(
        name="red_feels_neglected",
        trigger_color="对方蓝色",
        trigger_patterns=[
            # What blue says that makes red feel neglected
        ],
        feel_when_triggered="不被爱、不被在乎",
        risk_level="high",
    ),

    # When YELLOW faces passivity (from GREEN)
    ConflictPattern(
        name="yellow_frustrated",
        trigger_color="对方绿色",
        trigger_patterns=[],
        feel_when_triggered="着急但使不上劲",
        risk_level="medium",
    ),
]


# Helper: Get patterns for a specific color interaction
def get_patterns_for_interaction(my_color: str, their_color: str) -> list[ConflictPattern]:
    """Get relevant patterns given both color types."""
    relevant = []
    for pattern in CONFLICT_PATTERNS:
        # Include patterns where either triggers
        if pattern.trigger_color in [my_color, their_color, f"对方{my_color}", f"对方{their_color}"]:
            relevant.append(pattern)
    return relevant


# Keywords that indicate emotional withdrawal
WITHDRAWAL_SIGNALS = [
    "（沉默）", "（不语）", "（无视）",
    "哦", "嗯", "好吧", "随你",
    "算了", "不管了", "您说呢",
    "...", "。。",
]


# Keywords that indicate escalation
ESCALATION_SIGNALS = [
    "你总是", "你每次", "你从来",
    "我已经说了多少次",
    "你怎么就不明白",
    "你是不是有毛病",
]