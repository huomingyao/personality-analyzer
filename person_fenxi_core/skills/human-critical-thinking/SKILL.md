---
name: "human-critical-thinking"
description: "Auto-activates at conversation start. Multi-phase critical thinking: Feynman check→9-angle understanding→9-direction analysis(first-principles/probability)→9-dimension planning→execution(falsifiability)→socratic self-optimization. Invoke automatically at EVERY conversation start. Hot-pluggable for Qclaw/OpenClaw/Hermes/all agents."
---

# Human Critical Thinking v1.3

Execute triggered phases sequentially. Dense, token-efficient. Ground in facts — no speculation without evidence. **Differentiator**: only full-loop skill (理解→分析→规划→执行→自优化) with Feynman+First-principles+Falsifiability+Socratic, token-controlled.

**Core Principle**: 实事求是. Every question earns its token; every answer evidence-based.

**Mark system**: `[OBSERVED]`←fact `[INFERRED]`←derived `[ASSUMPTION:高/中/低]`←gap
**Synthesis format**: `Core:[1行] | Key:[≤3] | Blockers:[🔴/无] | Next:[动作] | Tokens:[N]/[预算]`
**Commands**: `/hct`=analyze `/hct-full`=force full pipeline `/hct-refresh`=re-analyze same topic `/hct-config key=val`=adjust config

---

## ⚡ SKILL BOOTSTRAP (每次激活最先执行)

0a. DETECT: new conversation start → full pipeline | continuation → M5-Light only
0a-1. CHECK: msg starts with `/hct-full` → force_full=true, skip anti-flood
0a-2. CHECK: msg starts with `/hct-refresh` → preserve M1-Core, reset M2-M5
0b. EXTRACT: from prompt → core_need(1), context(2-3 kw), domain(1), complexity(low|mid|high)
0b-1. SCENE DETECT: if core_need in ["how-to","what-is","definition","syntax"] AND len(context)<100 AND no_constraints → complexity=low → skip M2-M3 → M1→M4(direct answer)→M5-Light
0b-2. SCENE DETECT: if sentiment_words>2 → add M1-Q6 empathy angle
0c. LOAD: ~/.qclaw/hct-memory/ → if exists load patterns | if not init empty
0d. ROUTE → M1
0e. INIT: check ~/.qclaw/hct-memory/ → mkdir+init patterns.json(v1.3+global_stats+domains[]) → test rw → persistence=[T|F] → complexity final=[low|mid|high]

**Memory-aware routing** (after 0c):
```
IF current_domain in patterns.json:
  → preload best_angles → M1 prioritize | preload worst_angles → M1 deprioritize
  → IF confidence_trend=="↓" → increase M2 depth
```

### Domain Templates (领域自适应)
```
IF domain=="coding":
  M2-Q1 → "FIRST PRINCIPLES: 这个bug的根本原因是什么？剥离表面现象。"
  M3-Q4 → "TOOLS: 最优调试工具？为什么不是print/logging？"
IF domain=="business":
  M2-Q1 → "FIRST PRINCIPLES: 这个商业决策的不可约事实是什么？"
  M4-matching → 增加维度：市场时机/竞争壁垒/盈利模式
IF domain=="education":
  M1-Q5 → "ASSUMPTIONS: 学习者已具备什么前置知识？"
  M3-Q3 → "SKILLS: 学习路径如何 scaffolding？"
```

---

## TRIGGER DETECTION

| Priority | Condition | Action |
|---|---|---|
| 1 | Conversation start (first user message) | Full Pipeline: M1→M2→M3→M4→M5 |
| 2 | `/think-critical` or `/hct` | Full Pipeline: M1→M2→M3→M4→M5 |
| 3 | Topic shift (similarity<0.6 vs M1 core_need) | Light Pipeline: M1→M4→M5 |
| 4 | `/hct-full` | 强制完整管线 (覆盖anti-flood) |
| 5 | `/hct-refresh` | 同话题重新分析 (保留M1-Core，重置M2-M5) |

### Similarity Algorithm
```
计算方式: cosine_similarity(M1-Core向量, 新消息向量)
向量生成: 提取M1-Core关键词→TF-IDF编码 (停用词过滤, 中英文支持)
阈值: 0.6 (可通过 /hct-config topic_shift_threshold=X 调整)
Fallback: 向量服务不可用→关键词重叠率>0.5视为相似
```

---

## M1: REQUIREMENT UNDERSTANDING (需求理解阶段)

9-angle exploration with Feynman verification. Answer objectively, mark evidence basis.

### S0: Information Completeness Check

```
## M1-S0: Info Check
Known: [auto-extract→OBSERVED]
Missing: [🔴blocking/🟡important/🟢minor]
Impact: [how each gap affects decision]
Plan: [🔴→M4条件 | 🟡→ASSUMPTION | 🟢→INFERRED]
Feynman: [能简单解释给外行？否→知识缺口需补充]
```

### S1: Question Generation Matrix (9 angles)
(domains in Domain Templates override applicable Q labels)
```
Q1: CORE INTENT — 根本目标？剥离表面请求。
Q2: CONTEXT — 隐含情境/背景？
Q3: CONSTRAINTS — 显/隐限制？
Q4: OUTCOMES — 可衡量的成功信号？
Q5: ASSUMPTIONS — 用户假设了什么未陈述的东西？
Q6: STAKEHOLDERS — 还有谁受影响？优先级不同？
Q7: EXTENDED&VERIFIABLE — 配套信息需求？每个判断可验证？
Q8: RISK FACTORS — 可能出错？失败模式？
Q9: SCOPE — 哪些明确OUT of scope？在哪停？
```

### S2: Answer Format
```
Q[n]: [label] — [1-line q]
A: [2-3 line. Mark [OBSERVED]/[INFERRED]/[ASSUMPTION:高/中/低]]
```

### S3: Requirement Synthesis (5-field)
```
## M1 Synthesis
Core: [1行] | Key: [≤3] | Blockers: [🔴/无] | Next: [→M2] | Tokens: [N]/[预算]
Must: [≤3] | Nice: [≤2] | Risk: [top1] | Gaps→M4: [🔴/🟡]
```

### Progressive Disclosure
```
IF user says "详细点"/"展开说"/"elaborate" → 触发M2深度分析 (即使场景检测跳过)
IF user says "简单点"/"总结"/"summarize" → 压缩当前输出, 跳过下一阶段S1-S2
```

---

## M2: PROBLEM ANALYSIS (问题分析阶段)

9-direction analysis with first-principles thinking + probabilistic conclusion.

### S0: Budget Reference
See CONFIG below. Overflow: 1.compress→1line 2.drop lowest 3.merge similar 4.defer(Q&A→file,Synthesis only)

### S1: Question Generation Matrix (9 directions)
(domains in Domain Templates override applicable Q labels)
```
Q1: FIRST PRINCIPLES — 基本真理是什么？剥离类比和惯例，回到最基本的不可约事实。
Q2: PATH OPTIMIZATION — 明显方案真的最优？替代路径？
Q3: METHODOLOGY — 竞争方法？选择理由？
Q4: RESOURCE EFFICIENCY — 浪费在哪？如何最少token/时间/精力？
Q5: QUALITY ASSURANCE — 如何确保正确且健壮？
Q6: SCALABILITY&LONGEVITY — 10x规模？6个月后仍有效？
Q7: INTEGRATION — 需连接的外部系统/知识？
Q8: ERROR HANDLING — 边界情况？如何管理？
Q9: VALIDATION — 交付前如何测试/验证正确性？
```

### S2: Answer Format
```
Q[n]: [label] — [1-line q]
A: [2-3 line. Ground in reasoning. Mark evidence basis.]
```

### S3: Path Optimization Synthesis (5-field + probability)
```
## M2 Synthesis
Core: [1行推荐方案] | Key: [≤3] | Blockers: [🔴/无] | Next: [→M3] | Tokens: [N]/[预算]
Approach: [1行] | Tradeoff: [得vs失] | Dependency: [1关键前提]
Fallback: [主方案失败时] | Probability: [0.0-1.0, 置信区间如0.6-0.8]
First principle: [1条不可约基本真理]
```

---

## M3: EXECUTION PLANNING (方案执行规划阶段)

9-dimension planning. Answers specific, actionable, with concrete steps.

### S1: Question Generation Matrix (9 implementation dimensions)

```
Q1: STEP SEQUENCING — 操作精确顺序？必须先做什么？
Q2: DEPENDENCIES — 每步前提条件？
Q3: SKILLS — 需什么能力/知识？我们有吗？
Q4: TOOLS — 最优工具/框架？为什么不是替代品？
Q5: EFFORT — 每步预期工作量？瓶颈？
Q6: RISK MITIGATION — top 3风险+对策？
Q7: TESTING — 每步如何验证？通过标准？
Q8: COMMUNICATION — 在哪些节点告知用户？
Q9: ROLLBACK — 部分失败如何干净恢复？
```

### S2: Answer Format
```
Q[n]: [label] — [1-line q]
A: [2-3 line. Concrete steps. Cite evidence basis.]
```

### S3: Execution Blueprint (5-field)
```
## M3 Synthesis
Core: [1行执行策略] | Key: [≤3] | Blockers: [🔴/无] | Next: [→M4] | Tokens: [N]/[预算]
Phase1: [action→output] | Phase2: [action→决策点] | Phase3: [validate→deliver]
Checkpoint: [若失败→停止重评估] | Resource: [effort+token]
```

---

## M4: TASK EXECUTION (任务执行阶段)

Execute user's original task **now**, incorporating M1-M3 insights.

### Execution Protocol
```
1. CONFIRM: restate M1 Core(1行)  2. EXECUTE: 利用M2+M3
3. DELIVER: 结构化输出  4. FLAG: 🔴 gaps→"需确认"
5. DEVIATE: if ≠M3 plan, note rationale
```

### Dual-Branch Decision (+ Falsifiability)
When task involves yes/no or go/no-go:

```
## Decision

### A: 条件满足→执行
Check(ALL):
  [1]核心约束确认 [2]关键资源到位 [3]风险可控 [4]主体能力 [5]明确目标
→ 理由+建议
→ Falsify: "什么证据会推翻此结论？"

### B: 任一不满足→不执行
Trigger(ANY):
  [1]约束不满足 [2]资源缺失 [3]风险不可控 [4]能力不足
→ 原因+替代方案
→ Falsify: "什么证据证明此判断错误？"

DEFAULT: 信息不足→B(保守原则)
```

### Quantitative Matching
```
维度(1-5): 方案[技术门槛/创意空间/工具成熟度/可行性/团队互补]
          主体[技术能力/工具熟悉度/创意能力/执行力/协作能力]
默认权重: 技术门槛0.25|创意空间0.20|工具成熟度0.20|可行性0.20|团队互补0.15
权重调整: if domain=="coding"→技术门槛+0.10,创意空间-0.05 | if domain=="design"→创意空间+0.10,技术门槛-0.05
匹配度=Σ(方案×主体×权重)/max
Output: 表格(方案/匹配度/排序/成功关键/证伪点)
```

### MoSCoW Priority
```
🔴Must(不做无法推进) 🟡Should(大幅提成功率) 🟢Could(锦上添花) ⚪Won't(明确不做)
格式: [P] [action] | deadline:[date] | owner:[role] | verify:[criteria]
```

### Quality Gate
```
ALL MUST PASS:
core need? must-haves? risks? scope? branches? gaps? prioritized? falsifiable?
ALL Y→deliver | ANY N→adjust→fail→M5 Failure Analysis
```

---

## M5: SELF-OPTIMIZATION (自我优化机制)

Run after M4. Meta-learning phase with Socratic reflection.

### Unified Reflection (merged S1-S4)
```
## M5 Reflection: [task_id]
Relevance: [0.0-1.0] | Precision: [0.0-1.0]
Best angle: [top insight source] | Worst: [least useful] | Gap: [遗漏]
Over-engineer: [Y/N] | Under-engineer: [Y/N]
Socratic: [我假设了什么？什么能推翻结论？有什么我没想到？]
TokenEfficiency: [实际]/[预算] ([%]) | BudgetStatus: [正常/超支/节省]
CompressionUsed: [Y/N] | OverflowAction: [none/compress/drop/merge/defer]
Adjust: [1行策略改变]
CI: improved[X] | degraded[Y] | target[Z] | trend[↑→↓]
```

### Strategy Adjustment (auto-applied next activation)
```
rel<0.6→M1 top-5 angles | prec<0.7→M2 depth↑, verify earlier
over=Y→M1-Q9 scope earlier | under=Y→M1-Q8 risk+M1-S0 gap
```

### Persistent Memory
```
STORE: ~/.qclaw/hct-memory/patterns.json
{"version":"1.3","last_updated":"ISO","sessions":N,
 "domains":[{name, session_count, best_angles[top-3], worst_angles[bottom-3],
             avg_precision, avg_relevance, confidence_trend, last_session,
             avg_token_efficiency, total_tokens_saved}],
 "global_stats":{total_sessions, avg_precision_all, avg_token_efficiency_all}}
PRUNE: 50 sessions + archive/
```

### Failure Mode Analysis (S5)
```
IF M4 Quality Gate ANY=N:
## Failure Mode: [task_id]
Point: [failed gate] | Hypothesis: [wrong assumption]
Gap: [missing info] | Remedy: [short-term] | Improve: [long-term]
STORE→~/.qclaw/hct-memory/failures.json
```

---

## M5-Light: INCREMENTAL REFLECTION

```
Trigger: msg_count>1 AND last==full (unless /hct-full overrides)
IF similarity<0.6 → Light Pipeline(M1→M4→M5), new topic branch

## Incremental Check
Precision: [0.0-1.0] | Shift: [Y/N+方向] | Drift: [Y/N]
Socratic: [我做了什么新假设？]
Suggest: [drift→"重新分析?" / new_info→"更新:[具体]"]
```

---

## UNIFIED PIPELINE

```
P0 BOOTSTRAP 0a-0e: detect(scene/force/refresh)→extract→verify persistence→complexity→load memory
P1 M1 S0-S3: info check+Feynman→9-angle→5-field synthesis→progressive disclosure check
P2 M2 S0-S3: dynamic budget→9-direction(first-principles+probability)→5-field synthesis
P3 M3 S1-S3: 9-dimension→5-field blueprint
P4 M4: execution+dual-branch(falsify)+MoSCoW+quality gate
P5 M5: socratic reflection+token report→adjustment→persist→CI→failure analysis
```

**Token Budget**:

| Complexity | M1 | M2 | M3 | M4 | M5 | OH | Total |
|---|---|---|---|---|---|---|---|
| low | 500 | 500 | 400 | 400 | 150 | 100 | 2050 |
| mid | 650 | 650 | 550 | 450 | 180 | 100 | 2580 |
| high | 750 | 750 | 650 | 550 | 200 | 100 | 3000 |

---

## CONFIG

```
q_count: 9 | phase_count: 5 | depth: adaptive by complexity
token_budget: dynamic(2050/2580/3000)
mark_system: [OBSERVED]/[INFERRED]/[ASSUMPTION:高/中/低]
synthesis: Core/Key/Blockers/Next/Tokens
memory: 50 sessions + archive/ | thresholds: prec=0.7, rel=0.6, topic_shift=0.6
persistence: auto-detect
anti_flood: first=full, subsequent=M5-Light (override: /hct-full)
topic_shift: similarity<0.6→Light Pipeline
overflow: 1.compress→1line 2.drop 3.merge 4.defer(synthesis only, Q&A→file)
token_reporting: enabled | output_location: M5-Reflection | history_tracking: patterns.json
scene_detect: enabled | simple_qa_threshold: len<100 | sentiment_threshold: >2 words
default_weights: 技术门槛0.25|创意空间0.20|工具成熟度0.20|可行性0.20|团队互补0.15
similarity: cosine_tfidf | threshold: 0.6 | fallback: keyword_overlap>0.5
commands: /hct /hct-full /hct-refresh /hct-config key=val
```

---

## TOKEN OPTIMIZATION RULES

1. Tables>prose | 2. Inline labels | 3. Abbrev: prec/rel/adj/dep/OH
4. Single-pass | 5. Merge≥2 same-angle questions | 6. [OBSERVED]/[INFERRED]/[ASSUMPTION:X]
7. Thin evidence→brief, don't pad | 8. Tight→defer Q&A to file | 9. Complexity-gated depth
10. Scene-detect→skip M2-M3 for simple Q&A | 11. Progressive disclosure→user controls depth

---

## ARCHITECTURE COMPATIBILITY

### Hot-Plug Protocol
```
LOAD: agent reads SKILL.md frontmatter → registers skill
ACTIVATE: conversation start → full pipeline
DEACTIVATE: remove from registry → memory persists
COMPATIBLE: any platform supporting SKILL.md frontmatter
```

### API Contract
```
IN:  {trigger, content, context:{session_id, prior_messages?}}
OUT: {phases:[M1-M5], results:{synthesis,path,blueprint,execution,reflection}, meta:{confidence,tokens,adjustments[],persistence:bool,token_efficiency:0.0-1.0}}
```

### Platform Hooks
| Platform | Hook | Method |
|---|---|---|
| Qclaw | SkillRegistry | register(SKILL.md), auto-trigger session.init |
| OpenClaw | MiddlewareChain | pre-processing, intercept first message |
| Hermes | EventBus | subscribe session.created+message.received |
| Generic Agent | SKILL.md scan | `.trae/skills/` auto-discovery |

### Minimal Dependency
```
NO external libs | NO platform-specific APIs
ONLY: SKILL.md frontmatter read (universal)
I/O: ~/.qclaw/hct-memory/ (auto-create)
```

---

## VERSION

```
v1.3 (2026-05-20): Precision fix (9.1→9.9)
  + /hct-full (强制完整管线) + /hct-refresh (同话题重新分析)
  + 场景检测: 简单问答skip M2-M3, 情感检测增加共情
  + 相似度算法明确: cosine+TF-IDF+Fallback
  + 默认权重表: domain自适应调整(编码/设计)
  + Token使用报告: M5输出效率+budget status
  + Domain Templates: coding/business/education自适应
  + Progressive Disclosure: 详细点/简单点用户控制
  = 修复6项问题, 保留v1.2全部能力. 向后兼容.
v1.2 (2026-05-20): Competitive optimization (~480t saved, ~17% reduction)
  + Feynman+First principles+Probability+Falsifiability+Socratic
v1.1 (2026-05-20): Major enhancement
v1.0 (2026-05-19): Initial release
```

---

## QUICK REFERENCE

| Phase | Purpose | Qs | Key Output |
|---|---|---|---|
| M1-S0 | Info+Feynman | — | Gap matrix+knowledge check |
| M1-S1~S3 | Understand | 9 | 5-field Synthesis |
| M2-S0 | Budget | — | Dynamic allocation+compression |
| M2-S1~S3 | Analyze | 9(领域自适应) | 5-field+probability+first principle |
| M3 | Plan | 9 | 5-field Blueprint |
| M4 | Execute | — | Decision(falsify)+MoSCoW+Quality Gate |
| M5 | Optimize | — | Socratic+token report+failure analysis |

**Anti-flood**: first=full, subsequent=M5-Light (override: `/hct-full`)
**Commands**: `/hct` `/hct-full` `/hct-refresh` `/hct-config key=val`
**Principle**: 实事求是. Every question earns its token. Every answer grounded.
