import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


class SQLitePersistence:
    """Small SQLite-backed store for conversations, agent context, and reports."""

    def __init__(self, database_path: Optional[str] = None):
        self.database_path = database_path or str(Path(settings.data_dir) / "aesthetics_tutor.sqlite3")
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    session_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at
                ON chat_sessions(updated_at DESC)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    session_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY,
                    source_session_id TEXT NOT NULL,
                    chat_session_id TEXT,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(source_session_id, report_type)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_reports_created_at
                ON reports(created_at DESC)
                """
            )
            connection.execute("PRAGMA optimize")

    def save_chat_session(self, session_id: str, title: str, session_data: Dict[str, Any]) -> None:
        created_at = float(session_data.get("created_at", time.time()))
        updated_at = float(session_data.get("updated_at", time.time()))
        payload = json.dumps(session_data, ensure_ascii=False)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions(session_id, title, session_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    title = excluded.title,
                    session_json = excluded.session_json,
                    updated_at = excluded.updated_at
                """,
                (session_id, title, payload, created_at, updated_at),
            )

    def load_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT session_json FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return json.loads(row["session_json"]) if row else None

    def list_chat_sessions(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT session_id, title, created_at, updated_at,
                       json_array_length(json_extract(session_json, '$.messages')) AS message_count
                FROM chat_sessions
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def rename_chat_session(self, session_id: str, title: str) -> bool:
        session_data = self.load_chat_session(session_id)
        if not session_data:
            return False
        session_data["title"] = title
        session_data["updated_at"] = time.time()
        self.save_chat_session(session_id, title, session_data)
        return True

    def delete_chat_session(self, session_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            )
        return cursor.rowcount > 0

    def save_agent_session(self, session_id: str, agent_type: str, session_data: Dict[str, Any]) -> None:
        payload = json.dumps(session_data, ensure_ascii=False)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_sessions(session_id, agent_type, session_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    session_json = excluded.session_json,
                    updated_at = excluded.updated_at
                """,
                (
                    session_id,
                    agent_type,
                    payload,
                    session_data["created_at"],
                    session_data["last_active"],
                ),
            )

    def load_agent_sessions(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT session_json FROM agent_sessions"
            ).fetchall()
        return [json.loads(row["session_json"]) for row in rows]

    def delete_agent_session(self, session_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM agent_sessions WHERE session_id = ?", (session_id,))

    def archive_report(
        self,
        source_session_id: str,
        report_type: str,
        title: str,
        result: Dict[str, Any],
        chat_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        created_at = time.time()
        payload = json.dumps(result, ensure_ascii=False)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO reports(
                    report_id, source_session_id, chat_session_id, report_type,
                    title, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_session_id, report_type) DO UPDATE SET
                    chat_session_id = excluded.chat_session_id,
                    title = excluded.title,
                    result_json = excluded.result_json
                """,
                (
                    report_id,
                    source_session_id,
                    chat_session_id,
                    report_type,
                    title,
                    payload,
                    created_at,
                ),
            )
            row = connection.execute(
                "SELECT * FROM reports WHERE source_session_id = ? AND report_type = ?",
                (source_session_id, report_type),
            ).fetchone()
        return self._report_row(row)

    def list_reports(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reports ORDER BY created_at DESC"
            ).fetchall()
        return [self._report_row(row) for row in rows]

    def delete_report(self, report_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM reports WHERE report_id = ?", (report_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _report_row(row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["result"] = json.loads(data.pop("result_json"))
        return data


persistence = SQLitePersistence()
