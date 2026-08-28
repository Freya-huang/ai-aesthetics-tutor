import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from threading import Lock
from app.common.persistence import persistence


class SessionManager:
    ART_PREFIX = "art_"
    PAPER_PREFIX = "paper_"

    def __init__(self, max_history_per_session: int = 50):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.max_history_per_session = max_history_per_session
        self._restore_sessions()

    def _restore_sessions(self) -> None:
        for session in persistence.load_agent_sessions():
            session["created_at"] = datetime.fromisoformat(session["created_at"])
            session["last_active"] = datetime.fromisoformat(session["last_active"])
            for message in session.get("messages", []):
                if isinstance(message.get("timestamp"), str):
                    message["timestamp"] = datetime.fromisoformat(message["timestamp"])
            self._sessions[session["session_id"]] = session

    def _persist_session(self, session_id: str) -> None:
        session = self._sessions[session_id]
        serializable = {
            **session,
            "created_at": session["created_at"].isoformat(),
            "last_active": session["last_active"].isoformat(),
            "messages": [
                {
                    **message,
                    "timestamp": message["timestamp"].isoformat(),
                }
                for message in session["messages"]
            ],
        }
        persistence.save_agent_session(session_id, session["agent_type"], serializable)

    def _validate_session_id(self, session_id: str) -> bool:
        return session_id.startswith(self.ART_PREFIX) or session_id.startswith(
            self.PAPER_PREFIX
        )

    def create_session(self, agent_type: str = "art") -> str:
        if agent_type not in ("art", "paper"):
            raise ValueError(f"Unknown agent type: {agent_type}, must be 'art' or 'paper'")
        prefix = self.ART_PREFIX if agent_type == "art" else self.PAPER_PREFIX
        session_id = f"{prefix}{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._sessions[session_id] = {
                "session_id": session_id,
                "agent_type": agent_type,
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "messages": [],
            }
            self._persist_session(session_id)
        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if role not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid role: {role}")
        if not self._validate_session_id(session_id):
            raise ValueError(
                f"Invalid session_id format: {session_id}, must start with '{self.ART_PREFIX}' or '{self.PAPER_PREFIX}'"
            )
        with self._lock:
            if session_id not in self._sessions:
                agent_type = "art" if session_id.startswith(self.ART_PREFIX) else "paper"
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "agent_type": agent_type,
                    "created_at": datetime.now(),
                    "last_active": datetime.now(),
                    "messages": [],
                }
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
            }
            if extra:
                message.update(extra)
            self._sessions[session_id]["messages"].append(message)
            self._sessions[session_id]["last_active"] = datetime.now()
            if len(self._sessions[session_id]["messages"]) > self.max_history_per_session:
                self._sessions[session_id]["messages"] = self._sessions[session_id][
                    "messages"
                ][-self.max_history_per_session :]
            self._persist_session(session_id)

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        roles: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            if session_id not in self._sessions:
                return []
            messages = list(self._sessions[session_id]["messages"])
        if roles:
            messages = [m for m in messages if m["role"] in roles]
        if limit and limit > 0:
            messages = messages[-limit:]
        return messages

    def get_messages_for_llm(
        self,
        session_id: str,
        limit: Optional[int] = 20,
    ) -> List[Dict[str, str]]:
        messages = self.get_history(session_id, limit=limit)
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    def clear_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                persistence.delete_agent_session(session_id)
                return True
            return False

    def session_exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session = self._sessions[session_id]
            return {
                "session_id": session["session_id"],
                "agent_type": session["agent_type"],
                "created_at": session["created_at"].isoformat(),
                "last_active": session["last_active"].isoformat(),
                "message_count": len(session["messages"]),
            }

    def list_sessions(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            sessions = list(self._sessions.values())
        if agent_type:
            sessions = [s for s in sessions if s["agent_type"] == agent_type]
        return [
            {
                "session_id": s["session_id"],
                "agent_type": s["agent_type"],
                "created_at": s["created_at"].isoformat(),
                "last_active": s["last_active"].isoformat(),
                "message_count": len(s["messages"]),
            }
            for s in sessions
        ]


session_manager = SessionManager()
