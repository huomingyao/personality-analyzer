# 关系冲突预警系统 - 技术规格说明书

> 项目代号：RelationWarn
> 版本：v0.1 Draft

---

## 1. 产品愿景

**核心价值**：实时检测对话中的性格冲突点，预判关系风险

**差异化定位**：
- 现有系统：静态分析"TA是什么性格"
- 本系统：动态分析"我和TA的对话中，冲突点在哪里"

---

## 2. 核心功能

### 2.1 对话流分析

输入：一段对话（多轮交互）
```
我：你上次说的那个方案，我觉得有问题。
你：哪里有问题？
我：逻辑上不通啊，你没觉得吗？
你：（沉默）
```

输出：实时冲突标注
```
[
  {
    "turn": 2,
    "speaker": "我",
    "message": "逻辑上不通啊，你没觉得吗？",
    "type": "blue_logic_pressure",
    "risk_level": "medium",
    "reason": "用「逻辑」施压，可能触发红色用户的情感防御"
  },
  {
    "turn": 3,
    "speaker": "你",
    "message": "（沉默）",
    "type": "emotional_withdrawal",
    "risk_level": "high",
    "reason": "红色用户感受到被否定，选择回避"
  }
]
```

### 2.2 冲突模式库

| 模式 | A的行为 | B的感受 | 风险等级 |
|------|--------|--------|----------|
| **蓝→红频道错位** | 讲道理、列证据 | 被否定、不被理解 | 高 |
| **红→蓝频道错位** | 表达感受、求安慰 | 在逃、在回避 | 中 |
| **黄→绿节奏冲突** | 快节奏、催结果 | 太紧迫、压力好大 | 中 |
| **绿→黄被动攻击** | 不回应、等安排 | 没主见、靠不住 | 低 |
| **蓝→黄目标冲突** | 追求完美、纠细节 | 太挑剔、累不累 | 低 |
| **红→绿情感索取** | 一直倾诉、不听劝 | 被掏空、好累 | 高 |

### 2.3 实时预警（浏览器插件）

- 旁侧面板显示"当前对话风险指数"
- 每轮消息后给出简短提示
- 支持自定义提醒阈值

---

## 3. 技术架构

```
relation_warning/
├── backend/                    # 后端服务
│   ├── api/               # FastAPI 服务
│   ├── analyzer/          # 冲突分析引擎
│   └── models/           # 数据模型
│
├── frontend/                  # 浏览器插件
│   ├── manifest.json      # 插件清单
│   ├── sidepanel/       # 侧边面板 UI
│   └── content_script/ # 注入脚本
│
├── conflict_patterns/            # 冲突模式库
│   └── patterns.yaml
│
└── tests/                  # 测试
```

### 3.1 核心模块设计

```python
@dataclass
class Message:
    """单条消息"""
    turn: int              # 第几轮
    speaker: str          # 谁说的（我/对方）
    content: str          # 消息内容
    timestamp: str        # 时间戳


@dataclass
class ConflictSignal:
    """冲突信号"""
    turn: int
    speaker: str
    conflict_type: str      # 如 "blue_logic_pressure"
    risk_level: str      # high/medium/low
    reason: str        # 中文解释
    suggestion: str     # 建议如何回应


class ConflictAnalyzer:
    """冲突分析引擎"""

    def analyze(self, dialogue: list[Message]) -> list[ConflictSignal]:
        """分析对话流，返回冲突信号列表"""
        ...

    def compute_risk_index(self, signals: list[ConflictSignal]) -> float:
        """计算风险指数（0-100）"""
        ...
```

### 3.2 模式匹配引擎

两种检测方式：
1. **规则匹配** — 基于启发式规则（快速、准确）
2. **LLM 分析** — 调用大模型深度分析（灵活、可解释）

优先级：规则 → LLM（规则不确定时触发）

---

## 4. 冲突模式库详解

### 4.1 四大色彩的核心需求

| 色彩 | 核心需求 | 被满足时的表现 | 被忽视时的反应 |
|------|----------|------------|--------------|
| **红色** | 情感连接 | 热情、打开、倾诉 | 防御、沉默、逃离 |
| **蓝色** | 被理解 | 愿意分享细节 | 关闭、沉默、防备 |
| **黄色** | 被认可 | 有能量、行动派 | 抱怨、急躁、对抗 |
| **绿色** | 被接纳 | 配合、支持 | 退缩、被动 |

### 4.2 冲突触发器库

```yaml
patterns:
  - name: "蓝色逻辑施压"
    triggers_blue: []  # 蓝色说什么会触发
    triggers_red: []  # 红色说什么会触发
    red_feels: "被否定、不被理解"
    risk: "high"

  - name: "红色情感淹没"
    triggers_yellow: []
    triggers_green: []
    yellow_feels: "被迫倾听、好累"
    green_feels: "被掏空"
    risk: "high"
```

---

## 5. API 设计

### 5.1 分析接口

```
POST /analyze

Request:
{
  "dialogue": [
    {"turn": 1, "speaker": "我", "content": "你上次说的那个方案，我觉得有问题。"},
    {"turn": 2, "speaker": "对方", "content": "哪里有问题？"},
    {"turn": 3, "speaker": "我", "content": "逻辑上不通啊，你没觉得吗？"},
    {"turn": 4, "speaker": "对方", "content": "（沉默）"}
  ],
  "my_color": "蓝色",
  "their_color": "红色"
}

Response:
{
  "signals": [...],
  "risk_index": 72,
  "summary": "检测到高风险冲突，对方已表现出回避行为"
}
```

### 5.2 快速评估接口

```
GET /quick?q=<单条消息>&my_color=<>&their_color=<>
```

返回单条消息的风险评估（用于实时插件）

---

## 6. 验收标准

| 功能 | 验收条件 |
|------|----------|
| 对话分析 | 给出一段10轮对话，能产出信号列表 |
| 风险指数 | 计算出 0-100 的风险值 |
| 插件 Demo | Chrome 插件能加载，点击图标显示面板 |
| 准确率 | 人工抽样 90% 以上合理 |

---

## 7. 里程碑

- [x] M1: 冲突模式库原型（基于规则）
- [x] M2: 对话分析 API 服务
- [ ] M3: 浏览器插件 Demo ← 当前
- [ ] M4: 与 LLM 集成（可选）

---

*本文档为初始版本，随着开发推进持续迭代*