import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const API_TOKEN = process.env.API_TOKEN ?? "";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (API_TOKEN) headers["Authorization"] = `Bearer ${API_TOKEN}`;

  try {
    const upstream = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      return new Response(
        `data: ${JSON.stringify({ error: `Backend ${upstream.status}: ${text}` })}\n\ndata: [DONE]\n\n`,
        { status: 200, headers: { "Content-Type": "text/event-stream" } }
      );
    }

    // Pipe the SSE stream straight through to the browser
    return new Response(upstream.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
      },
    });
  } catch {
    return new Response(
      `data: ${JSON.stringify({ error: "Backend not running. Start it with: uvicorn api.main:app --reload" })}\n\ndata: [DONE]\n\n`,
      { status: 200, headers: { "Content-Type": "text/event-stream" } }
    );
  }
}
