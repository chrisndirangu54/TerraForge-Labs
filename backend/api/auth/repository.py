from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

from backend.api.auth.passwords import hash_password, verify_password
from backend.api.auth.settings import VALID_ROLES


class AuthRepository(ABC):
    @abstractmethod
    def create_user(
        self,
        email: str,
        password: str,
        display_name: str | None,
        role: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, email: str, password: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def create_project(self, slug: str, name: str, created_by: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_projects(self, user_id: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def add_membership(
        self, project_id: str, user_id: str, role: str
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_memberships(self, project_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class MemoryAuthRepository(AuthRepository):
    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}
        self._users_by_email: dict[str, str] = {}
        self._projects: dict[str, dict[str, Any]] = {}
        self._memberships: dict[tuple[str, str], dict[str, Any]] = {}

    def create_user(
        self,
        email: str,
        password: str,
        display_name: str | None,
        role: str,
    ) -> dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        if email in self._users_by_email:
            raise ValueError("Email already registered")
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": email.lower(),
            "password_hash": hash_password(password),
            "display_name": display_name,
            "role": role,
        }
        self._users[user_id] = user
        self._users_by_email[email.lower()] = user_id
        return self._public_user(user)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        user_id = self._users_by_email.get(email.lower())
        return self._users.get(user_id) if user_id else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        user = self._users.get(user_id)
        return self._public_user(user) if user else None

    def authenticate(self, email: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return self._public_user(user)

    def create_project(self, slug: str, name: str, created_by: str) -> dict[str, Any]:
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "slug": slug,
            "name": name,
            "created_by": created_by,
        }
        self._projects[project_id] = project
        self.add_membership(project_id, created_by, "admin")
        return project

    def list_projects(self, user_id: str | None = None) -> list[dict[str, Any]]:
        if user_id is None:
            return list(self._projects.values())
        project_ids = {
            project_id
            for (project_id, member_id) in self._memberships
            if member_id == user_id
        }
        return [self._projects[pid] for pid in project_ids if pid in self._projects]

    def add_membership(
        self, project_id: str, user_id: str, role: str
    ) -> dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        membership = {"project_id": project_id, "user_id": user_id, "role": role}
        self._memberships[(project_id, user_id)] = membership
        return membership

    def list_memberships(self, project_id: str) -> list[dict[str, Any]]:
        return [
            membership
            for (pid, _), membership in self._memberships.items()
            if pid == project_id
        ]

    @staticmethod
    def _public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": user["id"],
            "email": user["email"],
            "display_name": user.get("display_name"),
            "role": user["role"],
        }


class PostgresAuthRepository(AuthRepository):
    def create_user(
        self,
        email: str,
        password: str,
        display_name: str | None,
        role: str,
    ) -> dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        from backend.api.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users (email, password_hash, display_name, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, display_name, role
                """,
                (email.lower(), hash_password(password), display_name, role),
            ).fetchone()
            conn.commit()
        user = self._row_to_user(row)
        if user is None:
            raise RuntimeError("Failed to create user")
        return user

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        from backend.api.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, email, password_hash, display_name, role
                FROM users WHERE email = %s
                """,
                (email.lower(),),
            ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        from backend.api.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, email, display_name, role
                FROM users WHERE id = %s::uuid
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def authenticate(self, email: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return self._row_to_user(user)

    def create_project(self, slug: str, name: str, created_by: str) -> dict[str, Any]:
        from backend.api.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO projects (slug, name, created_by)
                VALUES (%s, %s, %s::uuid)
                RETURNING id, slug, name, created_by
                """,
                (slug, name, created_by),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO project_memberships (project_id, user_id, role)
                VALUES (%s::uuid, %s::uuid, 'admin')
                ON CONFLICT DO NOTHING
                """,
                (row["id"], created_by),
            )
            conn.commit()
        return {
            "id": str(row["id"]),
            "slug": row["slug"],
            "name": row["name"],
            "created_by": str(row["created_by"]),
        }

    def list_projects(self, user_id: str | None = None) -> list[dict[str, Any]]:
        from backend.api.db import get_connection

        with get_connection() as conn:
            if user_id:
                rows = conn.execute(
                    """
                    SELECT p.id, p.slug, p.name, p.created_by
                    FROM projects p
                    JOIN project_memberships m ON m.project_id = p.id
                    WHERE m.user_id = %s::uuid
                    ORDER BY p.name
                    """,
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, slug, name, created_by
                    FROM projects
                    ORDER BY name
                    """).fetchall()
        return [
            {
                "id": str(row["id"]),
                "slug": row["slug"],
                "name": row["name"],
                "created_by": str(row["created_by"]) if row["created_by"] else None,
            }
            for row in rows
        ]

    def add_membership(
        self, project_id: str, user_id: str, role: str
    ) -> dict[str, Any]:
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")
        from backend.api.db import get_connection

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO project_memberships (project_id, user_id, role)
                VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT (project_id, user_id)
                DO UPDATE SET role = EXCLUDED.role
                """,
                (project_id, user_id, role),
            )
            conn.commit()
        return {"project_id": project_id, "user_id": user_id, "role": role}

    def list_memberships(self, project_id: str) -> list[dict[str, Any]]:
        from backend.api.db import get_connection

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT project_id, user_id, role
                FROM project_memberships
                WHERE project_id = %s::uuid
                """,
                (project_id,),
            ).fetchall()
        return [
            {
                "project_id": str(row["project_id"]),
                "user_id": str(row["user_id"]),
                "role": row["role"],
            }
            for row in rows
        ]

    @staticmethod
    def _row_to_user(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "email": row["email"],
            "display_name": row.get("display_name"),
            "role": row["role"],
        }


_REPOSITORY: AuthRepository | None = None


def get_auth_repository() -> AuthRepository:
    global _REPOSITORY
    if _REPOSITORY is not None:
        return _REPOSITORY

    import os

    backend = os.getenv("AUTH_STORE_BACKEND", "").lower()
    if not backend:
        from backend.api.db import db_available

        backend = "postgres" if db_available() else "memory"

    if backend == "postgres":
        _REPOSITORY = PostgresAuthRepository()
    else:
        _REPOSITORY = MemoryAuthRepository()
    return _REPOSITORY


def reset_auth_repository() -> None:
    global _REPOSITORY
    _REPOSITORY = None
