"""Session management for state persistence."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from src.config import DATA_DIR


SESSION_DIR = DATA_DIR / "sessions"
SESSION_DIR.mkdir(exist_ok=True)


@dataclass
class SessionState:
    """Session state container."""

    session_id: str
    created_at: str
    updated_at: str
    user_id: str
    turns: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, user_id: str = "default") -> SessionState:
        """Create a new session."""
        now = datetime.utcnow().isoformat()
        return cls(
            session_id=str(uuid4()),
            created_at=now,
            updated_at=now,
            user_id=user_id,
        )


class SessionManager:
    """Manage conversation sessions."""

    def __init__(self, session_dir: Path = SESSION_DIR) -> None:
        self.session_dir = session_dir

    def create_session(self, user_id: str = "default") -> SessionState:
        """Create a new session."""
        session = SessionState.create(user_id)
        self._save(session)
        return session

    def get_session(self, session_id: str) -> SessionState | None:
        """Load existing session."""
        path = self._get_path(session_id)
        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data)

    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[SessionState]:
        """Get user's recent sessions."""
        sessions = []

        for path in self.session_dir.glob(f"{user_id}_*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                sessions.append(SessionState(**data))
            except Exception:
                continue

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions[:limit]

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
    ) -> SessionState | None:
        """Add a turn to session."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.turns.append({
            "user": user_message,
            "assistant": assistant_response,
        })
        session.updated_at = datetime.utcnow().isoformat()

        self._save(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        path = self._get_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _save(self, session: SessionState) -> None:
        """Save session to disk."""
        path = self._get_path(session.session_id)
        data = asdict(session)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _get_path(self, session_id: str) -> Path:
        """Get session file path."""
        return self.session_dir / f"{session_id}.json"


# Convenience functions
def create_new_session(user_id: str = "default") -> SessionState:
    """Create a new session."""
    manager = SessionManager()
    return manager.create_session(user_id)


def load_session(session_id: str) -> SessionState | None:
    """Load existing session."""
    manager = SessionManager()
    return manager.get_session(session_id)


def continue_session(
    session_id: str,
    user_message: str,
    assistant_response: str,
) -> SessionState | None:
    """Add turn to session."""
    manager = SessionManager()
    return manager.add_turn(session_id, user_message, assistant_response)