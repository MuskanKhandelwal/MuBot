"""Read-only views over MuBot state files for the web UI."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HEARTBEAT_PATH = DATA_DIR / "heartbeat-state.json"
LEARNINGS_PATH = DATA_DIR / "learnings.json"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def get_status() -> dict[str, Any]:
    state = _load_json(HEARTBEAT_PATH, {})
    learnings = _load_json(LEARNINGS_PATH, {})
    now = datetime.now(timezone.utc)

    followups = state.get("scheduled_followups", [])
    unsent = [f for f in followups if not f.get("sent")]
    overdue = 0
    for f in unsent:
        due = _parse_iso(f.get("due_at"))
        if due and due <= now:
            overdue += 1

    positives = learnings.get("positives", [])
    rejections = learnings.get("rejections", [])
    no_response = learnings.get("no_responses", [])
    total_tracked = len(positives) + len(rejections) + len(no_response)
    reply_rate = (len(positives) / total_tracked) if total_tracked else 0.0

    return {
        "daily_email_count": state.get("daily_email_count", 0),
        "pending_followups": len(unsent),
        "overdue_followups": overdue,
        "campaigns_paused": bool(state.get("campaigns_paused")),
        "pause_reason": state.get("pause_reason"),
        "last_run": state.get("last_run"),
        "reply_rate": round(reply_rate, 3),
        "total_tracked": total_tracked,
        "positives": len(positives),
        "rejections": len(rejections),
        "no_responses": len(no_response),
    }


def get_pipeline() -> list[dict[str, Any]]:
    """Group follow-ups by thread/entry into one row per outreach."""
    state = _load_json(HEARTBEAT_PATH, {})
    learnings = _load_json(LEARNINGS_PATH, {})
    now = datetime.now(timezone.utc)

    replied_companies = {
        p.get("company", "").lower()
        for p in learnings.get("positives", [])
        if p.get("company")
    }

    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "followups": [],
            "first_due": None,
            "next_due": None,
        }
    )

    for f in state.get("scheduled_followups", []):
        key = f.get("thread_id") or f.get("entry_id") or f.get("company", "")
        if not key:
            continue
        g = groups[key]
        if not g.get("company"):
            g["company"] = f.get("company", "")
            g["role"] = f.get("role", "")
            g["email"] = f.get("email", "")
            g["recipient_name"] = f.get("recipient_name", "")
            g["thread_id"] = f.get("thread_id", "")
            g["entry_id"] = f.get("entry_id", "")
        g["followups"].append(
            {
                "name": f.get("followup_name", ""),
                "due_at": f.get("due_at"),
                "sent": bool(f.get("sent")),
            }
        )

    rows = []
    for key, g in groups.items():
        fus = sorted(g["followups"], key=lambda x: x.get("due_at") or "")
        sent_count = sum(1 for f in fus if f["sent"])
        unsent = [f for f in fus if not f["sent"]]
        next_due_str = unsent[0]["due_at"] if unsent else None
        next_due = _parse_iso(next_due_str)
        is_overdue = bool(next_due and next_due <= now)

        company = g.get("company", "")
        has_replied = company.lower() in replied_companies

        if has_replied:
            status = "Replied"
        elif sent_count >= len(fus) and fus:
            status = "All sent"
        elif is_overdue:
            status = "Overdue"
        elif sent_count > 0:
            status = f"FU{sent_count} sent"
        else:
            status = "Awaiting FU1"

        rows.append(
            {
                "key": key,
                "company": company,
                "role": g.get("role", ""),
                "email": g.get("email", ""),
                "recipient_name": g.get("recipient_name", ""),
                "thread_id": g.get("thread_id", ""),
                "entry_id": g.get("entry_id", ""),
                "followups_total": len(fus),
                "followups_sent": sent_count,
                "next_due_at": next_due_str,
                "status": status,
                "replied": has_replied,
            }
        )

    rows.sort(key=lambda r: (not r["replied"], r["next_due_at"] or "9999"))
    return rows


def get_followups() -> list[dict[str, Any]]:
    state = _load_json(HEARTBEAT_PATH, {})
    now = datetime.now(timezone.utc)
    out = []
    for f in state.get("scheduled_followups", []):
        due = _parse_iso(f.get("due_at"))
        out.append(
            {
                "entry_id": f.get("entry_id"),
                "company": f.get("company"),
                "role": f.get("role"),
                "email": f.get("email"),
                "followup_name": f.get("followup_name"),
                "due_at": f.get("due_at"),
                "sent": bool(f.get("sent")),
                "overdue": bool(due and due <= now and not f.get("sent")),
            }
        )
    out.sort(key=lambda x: x.get("due_at") or "")
    return out


def get_learnings() -> dict[str, Any]:
    learnings = _load_json(LEARNINGS_PATH, {})
    positives = learnings.get("positives", [])
    rejections = learnings.get("rejections", [])
    no_response = learnings.get("no_responses", [])

    from collections import Counter

    role_counts = Counter(p.get("role_type", "other") for p in positives)
    rejection_roles = Counter(r.get("role_type", "other") for r in rejections)

    word_counts = [p.get("word_count") for p in positives if p.get("word_count")]
    avg_words = sum(word_counts) // len(word_counts) if word_counts else None

    return {
        "totals": {
            "positives": len(positives),
            "rejections": len(rejections),
            "no_responses": len(no_response),
        },
        "top_positive_role_types": role_counts.most_common(5),
        "top_rejected_role_types": rejection_roles.most_common(5),
        "avg_word_count_of_replies": avg_words,
        "recent_positives": positives[-5:],
    }
