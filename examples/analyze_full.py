"""
分析火铭遥的用户画像 - 完整版
"""

import requests
import json

BASE_URL = "http://localhost:8000"
WORKSPACE = "huomingyao-profile"

def create_test_data():
    # 创建工作空间
    requests.post(f"{BASE_URL}/v3/workspaces", json={"id": WORKSPACE})

    # 创建用户
    requests.post(f"{BASE_URL}/v3/workspaces/{WORKSPACE}/peers", json={"id": "huomingyao"})

    # 创建session
    requests.post(f"{BASE_URL}/v3/workspaces/{WORKSPACE}/sessions",
        json={"id": "full-review", "peer_ids": ["huomingyao"]})

    # 读取文档内容
    from docx import Document
    doc = Document('d:/person_fenxi/火铭遥 期中总结26.docx')
    content_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            content_parts.append(para.text)

    # 合并文本 - 分批发送
    full_text = "\n".join(content_parts)

    # 分段发送（每段限制约1500字符）
    chunk_size = 1500
    messages = []
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i+chunk_size]
        if chunk.strip():
            # 每4个chunk作为一个对话轮次
            chunk_idx = i // chunk_size
            if chunk_idx % 2 == 0:
                messages.append({"peer_id": "huomingyao", "content": chunk})
            else:
                messages.append({"peer_id": "system", "role": "assistant", "content": "收到，继续"})

    # 发送消息
    if messages:
        resp = requests.post(
            f"{BASE_URL}/v3/workspaces/{WORKSPACE}/sessions/full-review/messages",
            json={"messages": messages}
        )
        print(f"✓ 添加了 {len(messages)} 条消息, 总计约 {len(full_text)} 字符")

    return len(full_text)

def get_results():
    import time
    time.sleep(8)  # 等待处理

    # 查询结论
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{WORKSPACE}/conclusions/list",
        json={"peer_id": "huomingyao"}
    )
    result = resp.json()
    conclusions = result.get("items", [])

    print(f"\n{'='*60}")
    print(f"提取的用户画像 ({len(conclusions)} 个结论)")
    print(f"{'='*60}\n")

    for c in conclusions[:20]:  # 显示前20个
        print(f"• {c.get('content', '')}")

    # 查询表征
    resp = requests.post(
        f"{BASE_URL}/v3/workspaces/{WORKSPACE}/peers/huomingyao/representation",
        json={}
    )
    if resp.status_code == 200:
        repr_result = resp.json()
        print(f"\n{'='*60}")
        print("用户表征 (Representation)")
        print(f"{'='*60}")
        print(repr_result.get("representation", "")[:500])

    # 对话式查询
    print(f"\n{'='*60}")
    print("对话式分析")
    print(f"{'='*60}\n")

    queries = [
        "火铭遥是一个什么样的人？全面描述他的性格特点",
        "他的学习态度和动机是什么？有什么优势和短板？",
        "他在团队合作中表现如何？有什么反思？",
        "给他几句综合评价"
    ]

    for q in queries:
        resp = requests.post(
            f"{BASE_URL}/v3/workspaces/{WORKSPACE}/peers/huomingyao/chat",
            json={"query": q}
        )
        if resp.status_code == 200:
            result = resp.json()
            print(f"问: {q}")
            print(f"答: {result.get('content', '')[:400]}...")
            print()

if __name__ == "__main__":
    print("=" * 60)
    print("分析火铭遥的完整用户画像")
    print("=" * 60)

    print("\n[1] 创建工作空间和上传内容...")
    char_count = create_test_data()

    print("\n[2] 获取分析结果...")
    get_results()