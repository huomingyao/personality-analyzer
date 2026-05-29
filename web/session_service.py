"""Session management service for Psyche KB Web API."""
from __future__ import annotations

import sys
import os
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WEB_DIR)
for p in [ROOT, WEB_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Try to reuse existing session module
try:
    from person_fenxi_core.session import SessionManager as _CoreSessionManager
except ImportError:
    _CoreSessionManager = None

DATA_DIR = os.path.join(WEB_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")


@dataclass
class SessionData:
    """A single analysis session."""

    session_id: str
    target: str
    framework: str | None = None
    materials: str = ""
    status: str = "active"  # active | reviewing | completed
    results: list[dict[str, Any]] = field(default_factory=list)
    review_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "target": self.target,
            "framework": self.framework,
            "materials_length": len(self.materials),
            "status": self.status,
            "result_count": len(self.results),
            "review_count": len(self.review_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionService:
    """Manage analysis sessions with persistence."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._sessions: dict[str, SessionData] = {}
        self._load()

    def _load(self):
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for sid, sdata in data.items():
                    self._sessions[sid] = SessionData(**sdata)
            except Exception:
                pass

    def _save(self):
        data = {sid: vars(s) for sid, s in self._sessions.items()}
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def create(self, target: str, materials: str = "",
               framework: str | None = None) -> SessionData:
        """Create a new session."""
        sid = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        session = SessionData(
            session_id=sid,
            target=target,
            framework=framework,
            materials=materials,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self._sessions[sid] = session
        self._save()
        return session

    def get(self, session_id: str) -> SessionData | None:
        return self._sessions.get(session_id)

    def list_all(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._sessions.values()]

    def add_result(self, session_id: str, framework: str, result: str) -> bool:
        """Append an analysis result to a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.results.append({
            "framework": framework,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return True

    def add_review(self, session_id: str, review: dict[str, Any]) -> bool:
        """Append a review result to a session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.review_history.append(review)
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return True

    def update_status(self, session_id: str, status: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.status = status
        session.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return True

    def delete(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            return False
        del self._sessions[session_id]
        self._save()
        return True
