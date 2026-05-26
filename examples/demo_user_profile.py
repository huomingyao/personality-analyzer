"""
Honcho 用户画像示例（纯 HTTP API 版本）
使用本地部署的 Honcho 服务创建和管理用户画像
"""

import requests
import json
import time

# API 配置
BASE_URL = "http://localhost:8000"
WORKSPACE = "demo-workspace"

def create_workspace(name):
    """创建工作空间"""
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces",
        json={"id": name}
    )
    if resp.status_code in (200, 201):
        return resp.json()
    elif resp.status_code == 409:
        return {"id": name, "status": "already_exists"}
    raise Exception(f"Failed: {resp.text}")

def create_peer(workspace_id, peer_id):
    """创建用户/peer"""
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/peers",
        json={"id": peer_id}
    )
    if resp.status_code in (200, 201):
        return resp.json()
    elif resp.status_code == 409:
        return {"id": peer_id, "status": "already_exists"}
    raise Exception(f"Failed: {resp.text}")

def create_session(workspace_id, session_id, peer_ids):
    """创建对话 session"""
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/sessions",
        json={
            "id": session_id,
            "peer_ids": peer_ids
        }
    )
    if resp.status_code in (200, 201):
        return resp.json()
    elif resp.status_code == 409:
        return {"id": session_id, "status": "already_exists"}
    raise Exception(f"Failed: {resp.text}")

def add_messages(workspace_id, session_id, messages):
    """添加对话消息"""
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/sessions/{session_id}/messages",
        json={"messages": messages}
    )
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(f"Failed: {resp.text}")

def get_conclusions(workspace_id, peer_id=None):
    """获取结论列表"""
    if peer_id:
        resp = requests.post(
            f"{BASE_URL}/v3/workspaces/{workspace_id}/conclusions/list",
            json={"peer_id": peer_id}
        )
    else:
        resp = requests.get(
            f"{BASE_URL}/v3/workspaces/{workspace_id}/conclusions"
        )
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Failed: {resp.text}")

def get_representation(workspace_id, peer_id):
    """获取用户表征"""
    resp = requests.get(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/peers/{peer_id}/representation"
    )
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Failed: {resp.text}")

def get_peer_card(workspace_id, peer_id):
    """获取用户卡片"""
    resp = requests.get(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/peers/{peer_id}/card"
    )
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Failed: {resp.text}")

def chat(workspace_id, peer_id, query):
    """对话式查询"""
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{workspace_id}/peers/{peer_id}/chat",
        json={"query": query}
    )
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"Failed: {resp.text}")

def main():
    print("=" * 50)
    print("Honcho 用户画像示例")
    print("=" * 50)

    # ===== 1. 创建工作空间 =====
    print("\n=== 1. 创建工作空间 ===")
    ws = create_workspace(WORKSPACE)
    print(f"✓ 工作空间: {ws['id']}")

    # ===== 2. 创建用户 =====
    print("\n=== 2. 创建用户 ===")
    alice = create_peer(WORKSPACE, "alice")
    print(f"✓ 用户: {alice['id']}")

    # ===== 3. 创建对话 =====
    print("\n=== 3. 创建对话 ===")
    session = create_session(WORKSPACE, "session-1", ["alice"])
    print(f"✓ 会话: {session['id']}")

    # ===== 4. 添加对话消息 =====
    print("\n=== 4. 添加对话消息 ===")
    messages = [
        {"peer_id": "alice", "content": "你好！我是一名大学生正在学习人工智能。我对机器学习特别感兴趣"},
        {"peer_id": "system", "role": "assistant", "content": "太棒了！机器学习是 AI 的核心。你有什么基础吗？"},
        {"peer_id": "alice", "content": "我有 Python 基础，学过高数和线性代数。还看过一些深度学习的入门资料"},
        {"peer_id": "system", "role": "assistant", "content": "很好！你具备很好的数学基础。建议你可以从 TensorFlow 或 PyTorch 开始实践。有什么具体的项目想法吗？"},
        {"peer_id": "alice", "content": "我想做一个情绪分析的应用，可以分析用户评论是正面还是负面的"},
        {"peer_id": "system", "role": "assistant", "content": "这是很好的练手项目！你可以用 BERT 或 RoBERTa 这类预训练模型来做。数据标注是关键步骤。"}
    ]
    result = add_messages(WORKSPACE, "session-1", messages)
    print(f"✓ 添加了 {len(messages)} 条消息")

    # ===== 5. 等待画像生成 =====
    print("\n=== 5. 等待画像生成 ===")
    print("Honcho 会在后台自动提取用户特征...")
    print("等待 5 秒...")
    time.sleep(5)

    # ===== 6. 查看用户画像 =====
    print("\n=== 6. 查看结论 (Conclusions) ===")
    try:
        conclusions = get_conclusions(WORKSPACE, "alice")
        concl_list = conclusions.get("conclusions", [])
        print(f"✓ 共提取了 {len(concl_list)} 个结论:")
        for c in concl_list[:10]:
            level = c.get("level", "unknown")
            content = c.get("content", "")[:100]
            print(f"  • [{level}] {content}")
    except Exception as e:
        print(f"✗ 获取结论出错: {e}")

    # ===== 7. 获取用户表征 =====
    print("\n=== 7. 用户表征 (Representation) ===")
    try:
        rep = get_representation(WORKSPACE, "alice")
        print(f"✓ 用户表征:")
        print(json.dumps(rep, indent=2, ensure_ascii=False)[:800])
    except Exception as e:
        print(f"✗ 获取表征出错: {e}")

    # ===== 8. 用户卡片 =====
    print("\n=== 8. 用户卡片 (Card) ===")
    try:
        card = get_peer_card(WORKSPACE, "alice")
        print(f"✓ 用户卡片:")
        print(json.dumps(card, indent=2, ensure_ascii=False)[:800])
    except Exception as e:
        print(f"✗ 获取卡片出错: {e}")

    # ===== 9. 对话式查询 =====
    print("\n=== 9. 对话式查询 ===")
    try:
        response = chat(WORKSPACE, "alice", "alice 是一个什么样的人？她的兴趣是什么？")
        print(f"✓ 回答:")
        print(response.get("content", ""))
    except Exception as e:
        print(f"✗ 对话查询出错: {e}")

    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()