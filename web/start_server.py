# start_server.py - Psyche KB Web API (gevent version)

import os
import sys

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WEB_DIR)
for p in [WEB_DIR, ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from gevent import pywsgi
from psyche_kb import app

if __name__ == "__main__":
    # Create gevent WSGI server
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)

    print("===== Psyche KB Web API =====")
    print("🌐 本地访问: http://127.0.0.1:5000")
    print("🌐 局域网访问: http://本机IP:5000")
    print("🔧 按 Ctrl+C 停止服务")
    print("=============================\n")

    # Start server (supports concurrent connections)
    server.serve_forever()