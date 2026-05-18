"""FastAPI server exposing MuBot state and chat to the Next.js UI."""

from __future__ import annotations

import json
import os
from typing import Annotated

from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.state import (
    get_followups,
    get_learnings,
    get_pipeline,
    get_status,
)

API_TOKEN = os.environ.get("API_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]


def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
    if not API_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    if authorization.removeprefix("Bearer ").strip() != API_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid token")


app = FastAPI(title="MuBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Existing read-only endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", dependencies=[Depends(require_token)])
def status_endpoint() -> dict:
    return get_status()


@app.get("/pipeline", dependencies=[Depends(require_token)])
def pipeline_endpoint() -> list[dict]:
    return get_pipeline()


@app.get("/followups", dependencies=[Depends(require_token)])
def followups_endpoint() -> list[dict]:
    return get_followups()


@app.get("/learnings", dependencies=[Depends(require_token)])
def learnings_endpoint() -> dict:
    return get_learnings()


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


def _build_system_prompt() -> str:
    """Inject live MuBot state so the model can answer data questions accurately."""
    st = get_status()
    pipeline = get_pipeline()
    learnings = get_learnings()

    pipeline_summary = "\n".join(
        f"  - {r['company']} ({r['role']}): {r['status']}, next due {r['next_due_at'] or 'N/A'}"
        for r in pipeline[:20]  # cap to avoid huge prompts
    ) or "  (no pipeline entries)"

    return f"""You are MuBot, a personal AI job-search assistant for Muskan Khandelwal.
You help her track cold outreach campaigns, follow-ups, and reply rates.
Answer concisely and specifically using the live data below. Never make up numbers.

=== CURRENT STATUS ===
Emails sent today: {st['daily_email_count']}
Pending follow-ups: {st['pending_followups']}
Overdue follow-ups: {st['overdue_followups']}
Campaigns paused: {st['campaigns_paused']}{f" ({st['pause_reason']})" if st['pause_reason'] else ""}
Last heartbeat: {st['last_run'] or 'never'}

=== REPLY OUTCOMES ===
Positives: {st['positives']}
Rejections: {st['rejections']}
No response: {st['no_responses']}
Reply rate: {round(st['reply_rate'] * 100)}% ({st['positives']}/{st['total_tracked']} tracked)

=== PIPELINE (top 20) ===
{pipeline_summary}

=== LEARNINGS ===
Avg word count of positive replies: {learnings['avg_word_count_of_replies'] or 'N/A'}
Top positive role types: {learnings['top_positive_role_types']}
Top rejected role types: {learnings['top_rejected_role_types']}
"""


def _stream_chat(request: ChatRequest):
    """Yield SSE chunks from the OpenAI streaming response."""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        yield f"data: {json.dumps({'error': 'OPENAI_API_KEY not set in .env'})}\n\n"
        return

    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [{"role": "system", "content": _build_system_prompt()}]
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    try:
        with client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.4,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.post("/chat", dependencies=[Depends(require_token)])
def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_chat(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
