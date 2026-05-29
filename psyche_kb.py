"""psyche_kb.py - Psyche KB Web API 主入口"""

import os
import sys

# Path setup
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from flask import Flask, jsonify, request, render_template
from analyze_service import AnalyzeService
from critic_service import CriticService
from session_service import SessionService
from kb_browser import KnowledgeBrowser, create_browser

# 知识库 API
from kb_routes import kb_api

# ===================== Configuration =====================
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# ===================== Flask App =====================
app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.register_blueprint(kb_api)

# Lazily initialized services
_service = None
_critic_service = None
_session_service = None


def get_service() -> AnalyzeService:
    global _service
    if _service is None:
        _service = AnalyzeService()
    return _service


def get_critic() -> CriticService:
    global _critic_service
    if _critic_service is None:
        _critic_service = CriticService()
    return _critic_service


def get_session_svc() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service


# ===================== Routes =====================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/frameworks')
def api_frameworks():
    """Get available analysis frameworks"""
    try:
        frameworks = [
            {"id": "liangebodwo-mirror", "name": "陈海贤五层分析"},
            {"id": "九型人格", "name": "九型人格"},
            {"id": "性格色彩分析", "name": "性格色彩分析"}
        ]
        return jsonify({"success": True, "data": frameworks})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/skills')
def api_skills():
    """Get loaded skills status"""
    try:
        service = get_service()
        skills = service.get_available_skills()
        return jsonify({"success": True, "data": skills})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/kb/list', methods=['GET'])
def api_kb_list():
    """获取所有可用知识库列表（供 Agent 选择）"""
    try:
        browser = KnowledgeBrowser()
        bases = browser.list_knowledge_bases()
        return jsonify({"success": True, "data": bases})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/kb/structure', methods=['GET'])
def api_kb_structure():
    """获取知识库结构（文档列表）"""
    try:
        kb_name = request.args.get('name', '').strip()
        if not kb_name:
            return jsonify({"success": False, "message": "请指定知识库名称"})

        browser = KnowledgeBrowser(kb_name)
        structure = browser.get_kb_structure()
        return jsonify({"success": True, "data": structure})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/kb/search', methods=['GET'])
def api_kb_search():
    """知识库搜索（供 Agent 主动搜索）"""
    try:
        kb_name = request.args.get('name', '').strip()
        query = request.args.get('query', '').strip()

        if not kb_name or not query:
            return jsonify({"success": False, "message": "参数不完整"})

        browser = KnowledgeBrowser(kb_name)
        result = browser.search_by_keyword(query, max_docs=5)

        # 格式化结果
        docs = []
        for doc in result.documents:
            docs.append({
                "doc_id": doc.doc_id,
                "content": doc.content[:3000],  # 限制返回长度
                "sections": doc.sections,
            })

        return jsonify({"success": True, "data": {
            "query": query,
            "matches": len(docs),
            "documents": docs,
        }})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/kb/read', methods=['GET'])
def api_kb_read_doc():
    """读取知识库文档内容"""
    try:
        kb_name = request.args.get('name', '').strip()
        doc_id = request.args.get('doc_id', '').strip()

        if not kb_name or not doc_id:
            return jsonify({"success": False, "message": "参数不完整"})

        browser = KnowledgeBrowser(kb_name)
        content = browser.read_document_by_name(doc_id)

        if not content:
            return jsonify({"success": False, "message": "文档不存在"})

        return jsonify({"success": True, "data": {
            "doc_id": doc_id,
            "content": content[:10000],  # 限制返回长度
        }})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """心理分析 - 支持三种模式:
    1. 直接提供 materials
    2. 通过 kb_name + kb_search 让 Agent 主动搜索知识库
    3. auto_kb=true 让 Agent 自动从知识库加载材料
    """
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        materials = data.get('materials', '').strip()
        framework = data.get('framework', '').strip()

        # 新增：知识库模式
        kb_name = data.get('kb_name', '').strip()
        kb_search = data.get('kb_search', '').strip()  # Agent 主动搜索词
        auto_kb = data.get('auto_kb', False)  # 自动从知识库加载

        # 如果指定了知识库，使用知识库模式
        if kb_name:
            service = get_service()
            if auto_kb:
                # Agent 自动加载模式
                material_hint = data.get('material_hint', '')
                materials = service.auto_load_materials_from_kb(target, material_hint)
            # 使用知识库搜索模式
            result = service.analyze(
                target, materials, framework or None,
                kb_name=kb_name,
                kb_search=kb_search
            )
        else:
            # 传统模式：直接提供材料
            if not target:
                return jsonify({"success": False, "message": "请提供分析对象"})
            if not materials:
                return jsonify({"success": False, "message": "请提供分析材料"})

            service = get_service()
            result = service.analyze(target, materials, framework or None)

        return jsonify({"success": True, "data": {"result": result}})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/analyze/multi', methods=['POST'])
def api_analyze_multi():
    """Multi-framework combined analysis - 支持知识库模式"""
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        materials = data.get('materials', '').strip()
        frameworks = data.get('frameworks', [])

        # 支持知识库
        kb_name = data.get('kb_name', '').strip()
        kb_search = data.get('kb_search', '').strip()

        if kb_name:
            service = get_service()
            if kb_search:
                materials = service.search_knowledge_base(kb_search)
            else:
                structure = service.get_kb_structure()
                materials = f"[知识库: {kb_name}]\n{structure}"

        if not target:
            return jsonify({"success": False, "message": "请提供分析对象"})
        if not materials:
            return jsonify({"success": False, "message": "请提供分析材料"})
        if not frameworks:
            return jsonify({"success": False, "message": "请选择至少一个分析框架"})

        service = get_service()
        result = service.analyze_multi(target, materials, frameworks)

        return jsonify({"success": True, "data": {"result": result}})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/review', methods=['POST'])
def api_review():
    """Critic审查 - HCT质量守门人，支持三种模式:
    1. 直接提供 materials
    2. 通过 kb_name 让 Critic 从知识库获取原始材料
    3. verify_conclusions 让 Critic 主动搜索知识库验证分析结论
    """
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        materials = data.get('materials', '').strip()
        analysis = data.get('analysis', '').strip()
        framework = data.get('framework', '').strip()
        quick_only = data.get('quick_only', False)

        # 新增：知识库验证模式
        kb_name = data.get('kb_name', '').strip()
        verify_conclusions = data.get('verify_conclusions', False)  # 验证分析结论

        if not analysis:
            return jsonify({"success": False, "message": "请提供待审查的分析文本"})

        critic = get_critic()

        if quick_only:
            issues = critic.quick_check(analysis, framework or None)
            return jsonify({"success": True, "data": {
                "issues": issues,
                "passed": len(issues) == 0,
            }})

        # 支持知识库模式
        if kb_name:
            result = critic.review(
                target, materials, analysis, framework or None,
                kb_name=kb_name,
                verify_conclusions=verify_conclusions
            )
        else:
            result = critic.review(target, materials, analysis, framework or None)

        return jsonify({"success": True, "data": {
            "passed": result.passed,
            "decision": result.decision,
            "score": result.score,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "questions": result.questions,
            "suggestions": result.suggestions,
            "revision_notes": result.revision_notes,
            "raw_report": result.raw_report,
        }})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/analyze/with-review', methods=['POST'])
def api_analyze_with_review():
    """心理分析 + HCT自动审查循环（分析→审查→改进→...→输出）"""
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        materials = data.get('materials', '').strip()
        framework = data.get('framework', '').strip()

        if not target:
            return jsonify({"success": False, "message": "请提供分析对象"})
        if not materials:
            return jsonify({"success": False, "message": "请提供分析材料"})

        service = get_service()
        critic = get_critic()

        # Analyze → Review
        analysis = service.analyze(target, materials, framework or None)
        review = critic.review(target, materials, analysis, framework or None)

        # If not passed, retry once with revision notes
        retries = 0
        while not review.passed and retries < 2:
            retries += 1
            # Build retry prompt with critic feedback
            revision_prompt = service.build_revision_prompt(
                framework or "liangebodwo-mirror",
                target, materials, review.revision_notes
            )
            analysis = service.analyze_with_prompt(revision_prompt, framework or "liangebodwo-mirror")
            review = critic.review(target, materials, analysis, framework or None)

        return jsonify({"success": True, "data": {
            "result": analysis,
            "review": {
                "passed": review.passed,
                "decision": review.decision,
                "score": review.score,
                "strengths": review.strengths,
                "weaknesses": review.weaknesses,
                "questions": review.questions,
            },
            "retries": retries,
        }})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/session', methods=['GET', 'POST', 'DELETE'])
def api_session():
    """会话管理"""
    svc = get_session_svc()

    if request.method == 'GET':
        # 列所有会话 或 获取单个
        sid = request.args.get('id', '').strip()
        if sid:
            session = svc.get(sid)
            if not session:
                return jsonify({"success": False, "message": "会话不存在"})
            return jsonify({"success": True, "data": session.to_dict()})
        else:
            sessions = svc.list_all()
            return jsonify({"success": True, "data": sessions})

    elif request.method == 'POST':
        # 创建新会话
        data = request.get_json()
        target = data.get('target', '').strip()
        materials = data.get('materials', '').strip()
        framework = data.get('framework', '').strip()
        if not target:
            return jsonify({"success": False, "message": "请提供分析对象"})
        session = svc.create(target, materials, framework or None)
        return jsonify({"success": True, "data": session.to_dict()})

    elif request.method == 'DELETE':
        sid = request.args.get('id', '').strip()
        if not sid:
            return jsonify({"success": False, "message": "请提供会话ID"})
        ok = svc.delete(sid)
        return jsonify({"success": ok, "message": "已删除" if ok else "会话不存在"})


# ===================== Main =====================
if __name__ == "__main__":
    print("===== Psyche KB Web API =====")
    print(f"🌐 访问地址: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"🔧 按 Ctrl+C 停止服务")
    print("=============================\n")

    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=False,
        threaded=True
    )