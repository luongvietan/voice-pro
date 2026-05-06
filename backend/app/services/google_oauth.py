from __future__ import annotations

from typing import Any

import httpx


def fetch_google_userinfo(access_token: str) -> dict[str, Any]:
    with httpx.Client(timeout=15.0) as client:
        res = client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        res.raise_for_status()
        return res.json()
