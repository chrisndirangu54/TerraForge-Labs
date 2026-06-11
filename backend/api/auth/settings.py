from __future__ import annotations

import os

AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

VALID_ROLES = frozenset({"admin", "geologist", "contractor", "regulator_readonly"})
