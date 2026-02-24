from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any


class SessionsRepo:
    def __init__(self, db_path: str = "novel_flow.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    requirement_text TEXT NOT NULL,
                    spec_json TEXT,
                    proposal_json TEXT,
                    bible_json TEXT,
                    outline_full_json TEXT,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    bible_version INTEGER,
                    outline_version INTEGER,
                    last_user_action TEXT,
                    edit_text TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
            for column, ddl in (
                ("last_user_action", "ALTER TABLE sessions ADD COLUMN last_user_action TEXT"),
                ("edit_text", "ALTER TABLE sessions ADD COLUMN edit_text TEXT"),
                ("bible_json", "ALTER TABLE sessions ADD COLUMN bible_json TEXT"),
                ("outline_full_json", "ALTER TABLE sessions ADD COLUMN outline_full_json TEXT"),
                ("bible_version", "ALTER TABLE sessions ADD COLUMN bible_version INTEGER"),
                ("outline_version", "ALTER TABLE sessions ADD COLUMN outline_version INTEGER"),
            ):
                if column not in columns:
                    conn.execute(ddl)

    def create_session(self, text: str) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, requirement_text, spec_json, proposal_json, bible_json, outline_full_json,
                    status, version, bible_version, outline_version, last_user_action, edit_text
                )
                VALUES (?, ?, NULL, NULL, NULL, NULL, 'NEW', 0, NULL, NULL, NULL, NULL)
                """,
                (session_id, text),
            )
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if row is None:
            return None

        result = dict(row)
        for key in ("spec_json", "proposal_json", "bible_json", "outline_full_json"):
            if result[key]:
                result[key] = json.loads(result[key])
        return result

    def update_session(self, session_id: str, **fields: Any) -> None:
        if not fields:
            return

        assignments = []
        values = []
        for key, value in fields.items():
            db_key = key
            if key in {"spec_json", "proposal_json", "bible_json", "outline_full_json"} and value is not None:
                value = json.dumps(value)
            assignments.append(f"{db_key} = ?")
            values.append(value)

        assignments.append("updated_at = CURRENT_TIMESTAMP")
        values.append(session_id)

        query = f"UPDATE sessions SET {', '.join(assignments)} WHERE session_id = ?"
        with self._connect() as conn:
            conn.execute(query, values)
