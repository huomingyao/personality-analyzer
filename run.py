"""Personality Analyzer — 多框架人格分析系统启动入口

用法:
    python run.py              # 启动 Web 界面 (http://127.0.0.1:5000)
    python run.py --cli        # 命令行模式
"""

import os
import sys

# 确保项目根目录在 Python 路径中
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Personality Analyzer")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址 (默认 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="服务器端口 (默认 5000)")
    parser.add_argument("--cli", action="store_true", help="命令行交互模式")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        run_web(args.host, args.port)


def run_web(host: str, port: int):
    """启动 Web 界面"""
    print("===== Personality Analyzer =====")
    print(f"本地访问: http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    print("================================")

    # 使用 gevent 高性能服务器
    try:
        from gevent import pywsgi

        # 先确保路径正确
        web_dir = os.path.join(ROOT, "web")
        sys.path.insert(0, web_dir)

        from web.psyche_kb import app

        server = pywsgi.WSGIServer((host, port), app)
        server.serve_forever()
    except ImportError:
        # Fallback to Flask dev server
        web_dir = os.path.join(ROOT, "web")
        sys.path.insert(0, web_dir)

        from web.psyche_kb import app

        app.run(host=host, port=port, debug=False, threaded=True)


def run_cli():
    """命令行交互模式"""
    print("===== Personality Analyzer CLI =====")
    print("输入 'quit' 退出, 'frameworks' 查看可用框架")
    print("======================================")

    from person_fenxi_core.multi_framework_orchestrator import create_orchestrator

    orchestrator = create_orchestrator()

    while True:
        try:
            target = input("\n分析对象: ").strip()
            if target.lower() in ("quit", "exit", "q"):
                break
            if target.lower() == "frameworks":
                fws = orchestrator.skill_manager.find_available_frameworks()
                for fw in fws:
                    print(f"  - {fw['display_name']}: {fw['description']}")
                continue

            if not target:
                continue

            print("请输入材料（输入空行结束，Ctrl+D 结束）:")
            lines = []
            while True:
                try:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                except EOFError:
                    break
            materials = "\n".join(lines)

            if not materials:
                print("未输入材料")
                continue

            print("\n正在分析...")
            result = orchestrator.run_parallel_analysis(
                target=target,
                materials=materials,
                framework_ids=["性格色彩分析", "九型人格", "liangebodwo-mirror"],
            )

            print("\n" + "=" * 60)
            print(orchestrator.format_independent_reports(result))

        except KeyboardInterrupt:
            break

    print("\n再见!")


if __name__ == "__main__":
    main()
