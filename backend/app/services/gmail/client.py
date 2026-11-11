"""Minimal Gmail REST client (read-only). Uses httpx directly to keep dependencies small."""
import base64
import html
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import httpx

BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailError(Exception):
    pass


class GmailAuthError(GmailError):
    """Token invalid, expired beyond refresh, or revoked."""


class HistoryExpired(GmailError):
    """The stored history id is too old; a full sync is required."""


@dataclass
class ParsedMessage:
    id: str
    thread_id: str
    sender: str
    subject: str
    body: str
    html_body: str
    received_at: datetime


class GmailClient:
    def __init__(self, access_token: str, http: Optional[httpx.Client] = None):
        self._http = http or httpx.Client(timeout=30)
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def _get(self, path: str, params: Optional[dict] = None) -> httpx.Response:
        for attempt in range(4):
            r = self._http.get(BASE + path, params=params, headers=self._headers)
            if r.status_code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(min(float(r.headers.get("Retry-After", 2 ** attempt)), 10))
                continue
            break
        if r.status_code == 401:
            raise GmailAuthError("Gmail rejected the access token")
        return r

    def profile(self) -> dict:
        r = self._get("/profile")
        if r.status_code != 200:
            raise GmailError(f"Profile request failed ({r.status_code})")
        return r.json()

    def list_message_ids(self, query: str, limit: int) -> List[str]:
        ids: List[str] = []
        token = None
        while len(ids) < limit:
            params = {"q": query, "maxResults": min(100, limit - len(ids))}
            if token:
                params["pageToken"] = token
            r = self._get("/messages", params)
            if r.status_code != 200:
                raise GmailError(f"Message list failed ({r.status_code})")
            data = r.json()
            ids += [m["id"] for m in data.get("messages", [])]
            token = data.get("nextPageToken")
            if not token:
                break
        return ids[:limit]

    def history_message_ids(self, start_history_id: str) -> List[str]:
        ids: List[str] = []
        token = None
        while True:
            params = {"startHistoryId": start_history_id, "historyTypes": "messageAdded", "maxResults": 500}
            if token:
                params["pageToken"] = token
            r = self._get("/history", params)
            if r.status_code == 404:
                raise HistoryExpired()
            if r.status_code != 200:
                raise GmailError(f"History request failed ({r.status_code})")
            data = r.json()
            for item in data.get("history", []):
                ids += [m["message"]["id"] for m in item.get("messagesAdded", [])]
            token = data.get("nextPageToken")
            if not token:
                break
        return list(dict.fromkeys(ids))

    def get_message(self, message_id: str) -> Optional[dict]:
        r = self._get(f"/messages/{message_id}", {"format": "full"})
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise GmailError(f"Message fetch failed ({r.status_code})")
        return r.json()


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))).strip()


def _find_body(payload: dict) -> str:
    plain, html_part = [], []

    def walk(part: dict):
        mime = part.get("mimeType", "")
        data = (part.get("body") or {}).get("data")
        if data and mime == "text/plain":
            plain.append(_decode(data))
        elif data and mime == "text/html":
            html_part.append(_strip_html(_decode(data)))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return re.sub(r"\s+", " ", " ".join(plain)).strip() if plain else " ".join(html_part)


def _find_html(payload: dict) -> str:
    parts = []

    def walk(part: dict):
        data = (part.get("body") or {}).get("data")
        if data and part.get("mimeType") == "text/html":
            parts.append(_decode(data))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return "\n".join(parts)


def parse_message(msg: dict) -> ParsedMessage:
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    received = datetime.fromtimestamp(int(msg.get("internalDate", 0)) / 1000, tz=timezone.utc)
    return ParsedMessage(
        id=msg["id"], thread_id=msg.get("threadId", ""), sender=headers.get("from", ""),
        subject=headers.get("subject", ""), body=_find_body(payload) or msg.get("snippet", ""),
        html_body=_find_html(payload), received_at=received,
    )
