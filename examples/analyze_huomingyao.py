"""
分析火铭遥的用户画像
"""

import requests
import json

BASE_URL = "http://localhost:8000"
WORKSPACE = "student-profile"

# 火铭遥的期中总结内容
CONTENT = """
2026年春季学期PBL研究生P2班期中总结提纲

【运营工作】
在做饭上，开学排到了总共4次早饭，但是基本上每一次都是跟别人一起做的。做饭肯定能吃，炒菜也基本上没问题，就是慢吞吞的。如果我自己做的话，通常会把所有准备工作提前做完，要不然心虚。做饭能力，还是有不少提升空间的，打杂善后搞得比较干净……做饭就……
岗位的话，保持正常的干活，日常会抽大课间或者中午吃完饭、晚上吃完饭的时候去做一下岗位。工作基本是没有问题的，但是说是追求更好的境界，肯定是没有的。
公共卫生的话，还是可以的，打扫的自认为还是很干净的。
宿舍卫生上，就是正常搞吧，有时候会有一点敷衍。
内务上，搞得还算比较整齐吧。

【项目式学习感受】
这个学期的项目式学习变得很忙、很忙，事多的令人抓狂。和催命的似的，做这轮又有下一轮，想完了这个要想那个，还要跟项目的组员和指导老师进行各种的沟通，对于人际交往十分困难的人来说，每次交流之前，都需要提前做好心理准备，好恐怖……

不过这学期的项目式学习的氛围和之前有很大的变化，在做项目的时候，更有做项目的感觉了，还是挺好的。再就是，认知上的变化：这学期的项目式学习更多的是让我们学会去做项目这个本身的事情，更多是在做项目管理的事情。

觉得目前好的地方：对正式的做项目有了更多的了解，在项目管理上有了更新的认识。一个是茶子老师的一页纸项目管理，给出了一个系统的项目管理框架。

【对项目式学习的看法】
我觉得项目式学习，是在实践中去学习，而老师讲加上学生听只是理论层面的东西。在项目中去做学习，会有具体的事情背景，能够获得及时的反馈，学习才有效果。

【心性、思维和项目式学习的关系】
我觉得项目式学习，是把心性和思维应用出来的，也是在实践中去提升这两种能力。心性还是最重要的东西，项目要持续的进行下去，一直有动力前行，即便是遇到了问题也去积极解决，真的需要一颗十足的大心脏。

对我个人来说，知识难的问题是比较容易解决的问题。但是，最恐怖的是要组织团队一起去做这个项目，我对与人交往和人员管理上可以说一窍不通。沟通的时候，一紧张就不知道说什么了，说出来的和脑子里想的或者写纸上的就不一样了。所以，每次要和组员或者老师沟通的时候，就会处于压力山大的焦虑状态。

【团队角色的反思】
基本上都干过。发起人、组织者、决策者、跟进者、补漏者。

【个人职责边界反思】
我觉得我在个人职责边界上不是很明确。在很多的时候，容易多管闲事。很两难，感觉怎么搞都不是很合适。就是爱操心万一方案有问题怎么办，但是管的太宽，组员的能力就锻炼不到。

【体育活动体会】
松身功可以使身体更加松弛，能够使身体不那么僵硬。平衡性训练训练平衡能力。接抛球可以训练到专注力和手眼协调能力。我在练习这些内容的时候，有的体会就是运动课保持无脑，凭本能，混过运动课。

【各课程学习】
AI大语言应用：学习的主要内容是大语言模型课加部分实践项目。表现为还行，可进步可以���更多应用。
项目管理：上课少听了一次，实践的作业也没有参与。可进步课下实践。
思维课：学习辩论，批判性思维。表现正常上课。
数理化：没怎么学。可进步最好能混过合格考试。

【自我评分】85分
理由：一是在做项目以及项目的管理上仍有非常大的进步空间，二是在其他方面都有着很大的进步空间，三是在总结方面有有很大的进步空间。
"""

def create_workspace(name):
    resp = requests.post(f"{BASE_URL}/v3/workspaces", json={"id": name})
    return resp.json() if resp.status_code in (200, 201) else {"id": name}

def create_peer(workspace_id, peer_id):
    resp = requests.post(f"{BASE_URL}/v3/workspaces/{workspace_id}/peers", json={"id": peer_id})
    return resp.json() if resp.status_code in (200, 201) else {"id": peer_id}

def create_session(workspace_id, session_id, peer_ids):
    resp = requests.post(f"{BASE_URL}/v3/workspaces/{workspace_id}/sessions",
        json={"id": session_id, "peer_ids": peer_ids})
    return resp.json() if resp.status_code in (200, 201) else {"id": session_id}

def add_messages(workspace_id, session_id, content):
    # 将内容分段添加
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    messages = []
    for i, para in enumerate(paragraphs):
        peer = "huomingyao" if i % 2 == 0 else "system"
        role = None if i % 2 == 0 else "assistant"
        msg = {"peer_id": peer, "content": para}
        if role:
            msg["role"] = role
        messages.append(msg)

    resp = requests.post(f"{BASE_URL}/v3/workspaces/{workspace_id}/sessions/{session_id}/messages",
        json={"messages": messages})
    return resp.json()

def get_conclusions(workspace_id, peer_id):
    resp = requests.post(f"{BASE_URL}/v3/workspaces/{workspace_id}/conclusions/list",
        json={"peer_id": peer_id})
    return resp.json()

def chat(workspace_id, peer_id, query):
    resp = requests.post(f"{BASE_URL}/v3/workspaces/{workspace_id}/peers/{peer_id}/chat",
        json={"query": query})
    return resp.json()

def main():
    print("=" * 60)
    print("分析火铭遥的用户画像")
    print("=" * 60)

    # 创建工作空间
    print("\n[1] 创建工作空间...")
    create_workspace(WORKSPACE)
    print("✓ 完成")

    # 创建用户
    print("\n[2] 创建用户...")
    create_peer(WORKSPACE, "huomingyao")
    print("✓ 完成")

    # 创建session
    print("\n[3] 创建对话...")
    create_session(WORKSPACE, "midterm-review", ["huomingyao"])
    print("✓ 完成")

    # 添加消息 - 分段添加长内容
    print("\n[4] 添加内容到对话...")
    # 分成小块添加
    chunks = [
        CONTENT[i:i+3] for i in range(0, len([p for p in CONTENT.split('\n') if p.strip()]), 3)
    ]

    messages = []
    peer = "huomingyao"
    role = "assistant"
    for chunk in chunks:
        for para in chunk:
            messages.append({"peer_id": peer, "content": para})
            peer = "huomingyao" if peer != "huomingyao" else "huomingyao"
        messages.append({"peer_id": "system", "role": "assistant", "content": "了解了学生的分享，请继续"})

    # 简化：直接作为整体添加
    messages = [{"peer_id": "huomingyao", "content": CONTENT[:500]}]
    for i in range(0, len(CONTENT), 2000):
        chunk = CONTENT[i:i+2000]
        if chunk:
            messages.append({"peer_id": "huomingyao", "content": chunk})

    requests.post(f"{BASE_URL}/v3/workspaces/{WORKSPACE}/sessions/midterm-review/messages",
        json={"messages": [{"peer_id": "huomingyao", "content": CONTENT}]})
    print(f"✓ 添加了 {len(CONTENT)} 字符的内容")

    # 等待处理
    print("\n[5] 等待画像生成...")
    import time
    time.sleep(10)

    # 获取结论
    print("\n[6] 提取的用户画像 (Conclusions):")
    try:
        result = get_conclusions(WORKSPACE, "huomingyao")
        conclusions = result.get("items", [])
        print(f"共提取了 {len(conclusions)} 个结论:\n")
        for c in conclusions:
            print(f"  • {c.get('content', '')}")
    except Exception as e:
        print(f"获取失败: {e}")

    # 对话式查询
    print("\n[7] 对话式总结:")
    queries = [
        "huomingyao 是一个什么样的人？请全面描述他的性格特点",
        "他在项目式学习中表现如何？有什么优势和短板？",
        "他的学习态度和动机如何？"
    ]
    for q in queries:
        try:
            result = chat(WORKSPACE, "huomingyao", q)
            print(f"\n问: {q}")
            print(f"答: {result.get('content', '')[:300]}...")
        except Exception as e:
            print(f"  查询失败: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()