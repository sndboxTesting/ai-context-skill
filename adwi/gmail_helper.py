"""
Gmail helper for Adwi — Phase 1: read/search/thread/category (no mutation).
Uses OAuth2 with client credentials from secrets.local.env.
Token stored in secrets/gmail-token.json (never printed).
Scope: gmail.readonly — no sending, deleting, or modifying.

Phase 2 scope expansion (when ready): gmail.modify for archive/trash/mark-read.
Phase 3 scope expansion: gmail.compose + gmail.send for drafts/send.
"""
import json
import os
import base64
from pathlib import Path

SECRETS_DIR  = Path.home() / "SuneelWorkSpace" / "secrets"
CREDS_CACHE  = Path.home() / "Downloads" / "credentials.json"
TOKEN_FILE   = SECRETS_DIR / "gmail-token.json"
SCOPES       = ["https://www.googleapis.com/auth/gmail.readonly"]


def _load_secrets() -> dict:
    env_file = SECRETS_DIR / "secrets.local.env"
    d = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def get_service():
    """Return an authenticated Gmail service. Runs OAuth flow if needed."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            s = _load_secrets()
            client_config = {
                "installed": {
                    "client_id":     s.get("GOOGLE_CLIENT_ID", ""),
                    "client_secret": s.get("GOOGLE_CLIENT_SECRET", ""),
                    "project_id":    s.get("GOOGLE_PROJECT_ID", ""),
                    "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                    "token_uri":     "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            if not client_config["installed"]["client_id"]:
                raise RuntimeError("GOOGLE_CLIENT_ID not set in secrets.local.env")
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())
        TOKEN_FILE.chmod(0o600)

    return build("gmail", "v1", credentials=creds)


def _extract_body(payload: dict) -> str:
    """Extract plain-text body from a Gmail message payload (recursive)."""
    data = payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            d = part.get("body", {}).get("data", "")
            if d:
                return base64.urlsafe_b64decode(d).decode("utf-8", errors="replace")
        if part.get("parts"):
            result = _extract_body(part)
            if result:
                return result
    return ""


def list_emails(max_results=10, query="", inbox_only=True):
    """List recent emails newest-first. Returns dicts with thread_id included."""
    service = get_service()
    params = {"userId": "me", "maxResults": max_results * 2}
    if inbox_only and not query:
        params["labelIds"] = ["INBOX"]
    if query:
        if "label:" not in query and "in:" not in query:
            params["q"] = f"in:inbox {query}"
        else:
            params["q"] = query
    results = service.users().messages().list(**params).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        emails.append({
            "id":           msg["id"],
            "thread_id":    detail.get("threadId", ""),
            "subject":      headers.get("Subject", "(no subject)"),
            "from":         headers.get("From", ""),
            "date":         headers.get("Date", ""),
            "snippet":      detail.get("snippet", "")[:200],
            "internalDate": int(detail.get("internalDate", 0)),
        })

    emails.sort(key=lambda e: e["internalDate"], reverse=True)
    return emails[:max_results]


def read_email(msg_id: str) -> dict:
    """Read full text of an email by ID. Includes thread_id."""
    service = get_service()
    detail = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()
    headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
    body = _extract_body(detail.get("payload", {})) or detail.get("snippet", "")
    return {
        "id":        msg_id,
        "thread_id": detail.get("threadId", ""),
        "subject":   headers.get("Subject", "(no subject)"),
        "from":      headers.get("From", ""),
        "to":        headers.get("To", ""),
        "date":      headers.get("Date", ""),
        "body":      body[:5000],
    }


def get_thread(thread_id: str) -> dict:
    """Load all messages in a thread. Returns subject, count, and list of message dicts."""
    service = get_service()
    t = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    msgs = []
    for msg in t.get("messages", []):
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = _extract_body(msg.get("payload", {})) or msg.get("snippet", "")
        msgs.append({
            "id":      msg["id"],
            "from":    headers.get("From", ""),
            "to":      headers.get("To", ""),
            "date":    headers.get("Date", ""),
            "subject": headers.get("Subject", ""),
            "body":    body[:2000],
            "snippet": msg.get("snippet", ""),
        })
    subject = msgs[0]["subject"] if msgs else "(no subject)"
    return {
        "thread_id": thread_id,
        "subject":   subject,
        "messages":  msgs,
        "count":     len(msgs),
    }


def list_category(category: str = "INBOX", max_results: int = 10) -> list:
    """List emails by Gmail category label.
    category: INBOX, SPAM, CATEGORY_PROMOTIONS, CATEGORY_SOCIAL,
              CATEGORY_UPDATES, CATEGORY_FORUMS, UNREAD
    """
    service = get_service()
    params = {
        "userId":    "me",
        "maxResults": max_results * 2,
        "labelIds":  [category],
    }
    results = service.users().messages().list(**params).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        emails.append({
            "id":           msg["id"],
            "thread_id":    detail.get("threadId", ""),
            "subject":      headers.get("Subject", "(no subject)"),
            "from":         headers.get("From", ""),
            "date":         headers.get("Date", ""),
            "snippet":      detail.get("snippet", "")[:200],
            "internalDate": int(detail.get("internalDate", 0)),
        })
    emails.sort(key=lambda e: e["internalDate"], reverse=True)
    return emails[:max_results]


def get_label_counts() -> dict:
    """Get message counts for INBOX, UNREAD, SENT, SPAM."""
    service = get_service()
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    counts = {}
    for label in labels:
        if label["name"] in ("INBOX", "UNREAD", "SENT", "SPAM"):
            detail = service.users().labels().get(userId="me", id=label["id"]).execute()
            counts[label["name"]] = {
                "total":  detail.get("messagesTotal", 0),
                "unread": detail.get("messagesUnread", 0),
            }
    return counts
