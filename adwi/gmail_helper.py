"""
Gmail helper for Adwi — Phase 2: read/search/thread/category + archive/trash/mark-read.
Uses OAuth2 with client credentials from secrets.local.env.
Token stored in secrets/gmail-token.json (never printed).

Scope: gmail.modify — read + archive + trash + mark-read/unread (no send/compose).

Phase 2 scope change from readonly → modify:
  The existing token (if any) has readonly scope and will be rejected.
  Detection: get_service() checks token scopes and auto-prompts re-auth if needed.
  User step: run /gmail-auth once to re-authorize with the new scope.

Phase 3 scope expansion (when ready): gmail.compose + gmail.send for drafts/send.
"""
import json
import os
import base64
from pathlib import Path

SECRETS_DIR  = Path.home() / "SuneelWorkSpace" / "secrets"
TOKEN_FILE   = SECRETS_DIR / "gmail-token.json"
SCOPES       = ["https://www.googleapis.com/auth/gmail.modify"]


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
    """Return an authenticated Gmail service. Re-runs OAuth if scope mismatch."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        # Detect scope mismatch (e.g. old readonly token, now need modify)
        token_scopes = set(getattr(creds, "scopes", None) or [])
        required_scopes = set(SCOPES)
        if creds.valid and not required_scopes.issubset(token_scopes):
            creds = None  # Force re-auth to pick up expanded scopes

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None  # Refresh failed — full re-auth needed

    if not creds or not creds.valid:
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
    """Load all messages in a thread."""
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
    return {"thread_id": thread_id, "subject": subject, "messages": msgs, "count": len(msgs)}


def list_category(category: str = "INBOX", max_results: int = 10) -> list:
    """List emails by Gmail category label."""
    service = get_service()
    params = {"userId": "me", "maxResults": max_results * 2, "labelIds": [category]}
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


# ── Phase 2: mutation helpers (require gmail.modify scope) ────────────────────

def _batch_modify(msg_ids: list, add_labels: list = None, remove_labels: list = None) -> int:
    """Apply a label modification to a batch of messages. Returns count processed."""
    if not msg_ids:
        return 0
    service = get_service()
    body = {}
    if add_labels:    body["addLabelIds"] = add_labels
    if remove_labels: body["removeLabelIds"] = remove_labels
    # Gmail batchModify accepts up to 1000 IDs per call
    for i in range(0, len(msg_ids), 1000):
        service.users().messages().batchModify(
            userId="me",
            body={"ids": msg_ids[i:i+1000], **body}
        ).execute()
    return len(msg_ids)


def archive_messages(msg_ids: list) -> int:
    """Archive messages (remove INBOX label). Returns count modified."""
    return _batch_modify(msg_ids, remove_labels=["INBOX"])


def trash_messages(msg_ids: list) -> int:
    """Move messages to Trash. Uses individual trash() calls for correct semantics."""
    if not msg_ids:
        return 0
    service = get_service()
    count = 0
    for mid in msg_ids:
        service.users().messages().trash(userId="me", id=mid).execute()
        count += 1
    return count


def mark_read(msg_ids: list) -> int:
    """Mark messages as read (remove UNREAD label). Returns count modified."""
    return _batch_modify(msg_ids, remove_labels=["UNREAD"])


def mark_unread(msg_ids: list) -> int:
    """Mark messages as unread (add UNREAD label). Returns count modified."""
    return _batch_modify(msg_ids, add_labels=["UNREAD"])
