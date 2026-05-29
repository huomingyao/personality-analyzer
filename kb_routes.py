"""知识库管理 API - 支持在线上传和分析（Corpus2Skill 流水线）"""

import os
import time
import uuid
from pathlib import Path
from flask import (
    Blueprint, request, jsonify
)

ALLOWED_EXTENSIONS = {'txt', 'md', 'json', 'docx', 'pdf'}

# 引用 kb_service 中的 extract_text 和 Corpus2Skill 流水线
from kb_service import extract_text, _read_file

# 知识库存放目录
KB_BASE_DIR = r"D:\person_fenxi\web_api\knowledge_bases"

# 创建 Blueprint
kb_api = Blueprint('kb', __name__, url_prefix='/api/kb')


def _ensure_kb_dir():
    """确保知识库目录存在"""
    os.makedirs(KB_BASE_DIR, exist_ok=True)


def _get_kb_path(kb_name: str) -> str:
    """获取知识库路径"""
    safe_name = "".join(c for c in kb_name if c not in r'<>:"/\|?*')
    return os.path.join(KB_BASE_DIR, safe_name)


def _list_knowledge_bases():
    """获取所有知识库列表"""
    _ensure_kb_dir()
    bases = []
    for name in os.listdir(KB_BASE_DIR):
        path = os.path.join(KB_BASE_DIR, name)
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            bases.append({
                "id": name,
                "name": name,
                "file_count": len(files),
                "created": time.strftime("%Y-%m-%d"),
                "files": files
            })
    return bases


# ===================== 知识库 API =====================

@kb_api.route('/list', methods=['GET'])
def api_kb_list():
    """获取所有知识库列表"""
    try:
        bases = _list_knowledge_bases()
        return jsonify({"success": True, "data": bases})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/create', methods=['POST'])
def api_kb_create():
    """创建新知识库"""
    try:
        data = request.get_json()
        kb_name = data.get('name', '').strip()

        if not kb_name:
            return jsonify({"success": False, "message": "知识库名称不能为空"})

        kb_path = _get_kb_path(kb_name)
        if os.path.exists(kb_path):
            return jsonify({"success": False, "message": f"知识库[{kb_name}]已存在"})

        os.makedirs(kb_path)
        return jsonify({"success": True, "message": f"知识库[{kb_name}]创建成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/delete', methods=['POST'])
def api_kb_delete():
    """删除知识库"""
    try:
        data = request.get_json()
        kb_name = data.get('name', '').strip()

        if not kb_name:
            return jsonify({"success": False, "message": "知识库名称不能为空"})

        kb_path = _get_kb_path(kb_name)
        if not os.path.exists(kb_path):
            return jsonify({"success": False, "message": f"知识库[{kb_name}]不存在"})

        import shutil
        shutil.rmtree(kb_path)
        return jsonify({"success": True, "message": f"知识库[{kb_name}]删除成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/upload', methods=['POST'])
def api_kb_upload():
    """上传文件到知识库"""
    try:
        kb_name = request.form.get('kb_name', '').strip()
        if not kb_name:
            return jsonify({"success": False, "message": "请选择知识库"})

        kb_path = _get_kb_path(kb_name)
        os.makedirs(kb_path, exist_ok=True)

        if 'file' not in request.files:
            return jsonify({"success": False, "message": "请选择文件"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "文件名不能为空"})

        # 安全文件名 + 扩展名检查
        safe_name = "".join(c for c in file.filename if c not in r'<>:"/\|?*')
        ext = os.path.splitext(safe_name)[1].lower().lstrip('.')
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"success": False, "message": f"不支持的文件类型: .{ext}"})

        file_path = os.path.join(kb_path, safe_name)
        file.save(file_path)

        # 读取预览
        preview = extract_text(Path(file_path))[:500]

        # === Corpus2Skill 流水线：分块 + 索引 ===
        from kb_service import process_document
        pipeline_result = process_document(Path(file_path), kb_name)

        return jsonify({
            "success": True,
            "message": f"文件[{safe_name}]上传成功",
            "filename": safe_name,
            "preview": preview,
            "pipeline": {
                "chunk_count": pipeline_result.get("chunk_count", 0),
                "doc_id": pipeline_result.get("doc_id", ""),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/files', methods=['GET'])
def api_kb_files():
    """获取知识库文件列表"""
    try:
        kb_name = request.args.get('name', '').strip()
        if not kb_name:
            return jsonify({"success": False, "message": "请指定知识库"})

        kb_path = _get_kb_path(kb_name)
        if not os.path.exists(kb_path):
            return jsonify({"success": False, "message": "知识库不存在"})

        files = []
        for f in os.listdir(kb_path):
            fpath = os.path.join(kb_path, f)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                files.append({
                    "name": f,
                    "size": size,
                    "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(fpath)))
                })

        return jsonify({"success": True, "data": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/read', methods=['GET'])
def api_kb_read():
    """读取知识库文件内容"""
    try:
        kb_name = request.args.get('kb_name', '').strip()
        filename = request.args.get('filename', '').strip()

        if not kb_name or not filename:
            return jsonify({"success": False, "message": "参数不完整"})

        kb_path = _get_kb_path(kb_name)
        file_path = os.path.join(kb_path, filename)

        if not os.path.exists(file_path):
            return jsonify({"success": False, "message": "文件不存在"})

        content = _read_file(file_path)
        return jsonify({"success": True, "data": {"content": content}})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/tree', methods=['GET'])
def api_kb_tree():
    """获取知识库的知识树（Corpus2Skill INDEX）"""
    try:
        kb_name = request.args.get('name', '').strip()
        if not kb_name:
            return jsonify({"success": False, "message": "请指定知识库"})

        from kb_service import get_kb_tree
        tree = get_kb_tree(kb_name)
        return jsonify({"success": True, "data": tree})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/chunks', methods=['GET'])
def api_kb_chunks():
    """获取某个文档的分块"""
    try:
        kb_name = request.args.get('kb_name', '').strip()
        doc_id = request.args.get('doc_id', '').strip()
        if not kb_name or not doc_id:
            return jsonify({"success": False, "message": "参数不完整"})

        from kb_service import get_document_chunks
        chunks = get_document_chunks(kb_name, doc_id)
        return jsonify({"success": True, "data": chunks})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@kb_api.route('/content', methods=['GET'])
def api_kb_content():
    """获取知识库的全部内容（用于分析）"""
    try:
        kb_name = request.args.get('name', '').strip()
        if not kb_name:
            return jsonify({"success": False, "message": "请指定知识库"})

        kb_path = _get_kb_path(kb_name)
        if not os.path.exists(kb_path):
            return jsonify({"success": False, "message": "知识库不存在"})

        contents = []
        for f in os.listdir(kb_path):
            fpath = os.path.join(kb_path, f)
            if os.path.isfile(fpath):
                text = _read_file(fpath)
                contents.append(f"# {f}\n{text}")

        full_content = "\n\n".join(contents)
        return jsonify({
            "success": True,
            "data": {
                "kb_name": kb_name,
                "content": full_content,
                "length": len(full_content)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})