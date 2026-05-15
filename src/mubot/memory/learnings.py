"""Tracks what email patterns get replies and what doesn't."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from mubot.memory.models import OutreachEntry, ResponseCategory


class LearningsTracker:
    def __init__(self, base_path: Path):
        self.path = Path(base_path) / "learnings.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"positives": [], "rejections": [], "no_responses": []}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def log_response(self, entry: OutreachEntry, category: ResponseCategory, response_body: str = ""):
        record = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "company": entry.company_name,
            "role": entry.role_title,
            "role_type": self._categorize_role(entry.role_title),
            "subject": entry.subject,
            "word_count": len(entry.body.split()),
            "followup_count": entry.followup_count,
        }

        if category in (ResponseCategory.POSITIVE, ResponseCategory.NEEDS_REPLY, ResponseCategory.NEUTRAL):
            record["response_preview"] = response_body[:150]
            record["category"] = category.value
            self._data["positives"].append(record)
        elif category == ResponseCategory.REJECTION:
            self._data["rejections"].append(record)
        elif category == ResponseCategory.NO_RESPONSE:
            self._data["no_responses"].append(record)
        else:
            return

        self._save()

    def get_summary(self) -> str:
        positives = self._data.get("positives", [])
        rejections = self._data.get("rejections", [])
        no_responses = self._data.get("no_responses", [])
        total = len(positives) + len(rejections) + len(no_responses)

        if total == 0:
            return "No learnings yet — replies will be tracked here as they come in."

        interested = [p for p in positives if p.get("category") in ("positive", "needs-reply", None)]
        neutral_replies = [p for p in positives if p.get("category") == "neutral"]

        lines = [f"Outreach learnings from {total} tracked emails:"]
        lines.append(
            f"  Interested/engaged: {len(interested)}  |  Neutral: {len(neutral_replies)}  |  Rejections: {len(rejections)}  |  No response: {len(no_responses)}"
        )
        if total > 0:
            lines.append(f"  Reply rate: {len(positives)/total:.0%}  |  Positive rate: {len(interested)/total:.0%}")

        if positives:
            lines.append("\nWhat got replies (most recent 5):")
            for p in positives[-5:]:
                cat = p.get("category", "positive")
                lines.append(f"  • {p['company']} ({p['role_type']}) [{cat}]")
                lines.append(f"    Subject: \"{p['subject']}\"")
                preview = p.get("response_preview", "").strip()
                if preview:
                    lines.append(f"    Reply: \"{preview[:120]}\"")

            role_counts = Counter(p["role_type"] for p in interested)
            top = role_counts.most_common(3)
            if top:
                lines.append(f"\n  Best-performing role types: {', '.join(f'{r} ({c})' for r, c in top)}")

            word_counts = [p["word_count"] for p in positives if p.get("word_count")]
            if word_counts:
                lines.append(f"  Avg word count that worked: {sum(word_counts)//len(word_counts)} words")

            followup_wins = [p["followup_count"] for p in positives if p.get("followup_count", 0) > 0]
            if followup_wins:
                lines.append(f"  Replies from follow-ups: {len(followup_wins)} (follow-ups work!)")

        if rejections:
            lines.append(f"\nRejections ({len(rejections)} total):")
            rejection_roles = Counter(r["role_type"] for r in rejections)
            top_rejected = rejection_roles.most_common(2)
            if top_rejected:
                lines.append(f"  Most rejected role types: {', '.join(r for r, _ in top_rejected)}")

        return "\n".join(lines)

    def _categorize_role(self, role: str) -> str:
        r = role.lower()
        if "data engineer" in r:
            return "data_engineer"
        if any(k in r for k in ["data scientist", "data science"]):
            return "data_scientist"
        if any(k in r for k in ["ml engineer", "machine learning"]):
            return "ml_engineer"
        if any(k in r for k in ["ai engineer", "applied scientist"]):
            return "ai_engineer"
        if any(k in r for k in ["software engineer", "swe", "backend", "fullstack"]):
            return "software_engineer"
        if "analyst" in r:
            return "analyst"
        return "other"
