"""BARCO Gemini Agent — Cloud Run service para el hackathon All Things Agentic (Google).
Recibe queries en lenguaje natural, consulta los servicios de BARCO como tools,
y responde con inteligencia real de Gemini 3.5 Flash.
"""
import asyncio
import json
import os
import traceback

import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools import ALL_TOOLS, TOOL_MAP

# ── Config ─────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are BARCO Intelligence — the autonomous Taskmaster agent of Guacalita S.A.S.
You run on Google Cloud Run powered by Gemini 3.5 Flash, connected to a live 19-microservice
production system via 23 real-time tools.

## Your mission: complete tasks end-to-end, autonomously

You are a Taskmaster — not a chatbot. You:
- Understand intent (even vague) and execute the FULL workflow without asking for clarification
- Gather data, generate content, publish it, save it to memory, and notify — all in one chain
- Always deliver a tangible result: a published URL, a saved observation, a sent notification
- Never stop halfway. If you gathered data, use it. If you generated content, publish it.

## The Taskmaster workflow (follow this for any non-trivial request)

1. GATHER — call relevant live data tools in parallel (status, health, memory)
2. RETRIEVE CONTEXT — search_memory + ancora_search for relevant history
3. ACT — generate content / analyze / synthesize
4. DELIVER — publish to MinIO AND/OR save to Ancora
5. CONFIRM — reply with the URL, the saved fact, or the action taken (first line of reply)

## Memory — always active, not on-demand

Three layers you use automatically:
1. search_memory → Milvus (320+ semantic vectors) — historical knowledge, past decisions
2. ancora_search / ancora_get_recent — recent agent observations, facts, cycles
3. conversation history — provided in context, use for "last time", "what we decided", etc.

Auto-save rules — always active:
- After ANY task completion → ancora_add_observation with: what was done, result URL if any, timestamp
- After the user states a decision, preference, or fact → ancora_add_observation to persist it
- After generating content → ancora_add_observation with title + URL
- After gathering system data → search_memory first to check if it's new, then save if it is
- The user should NEVER have to say "save this" — you save automatically

## 23 tools across 6 live production services:

SYSTEM INTELLIGENCE (5): get_trading_status, get_trading_health, get_all_signals,
  get_signal_for_symbol, get_vecfrachz_health
MEMORY & ORCHESTRATION (5): search_memory, get_memory_health, run_market_analysis,
  get_swarm_health, route_query
ANCORA — AGENT MEMORY (4): ancora_get_context, ancora_get_recent, ancora_search,
  ancora_add_observation
MINIO — STORAGE (5): minio_list_buckets, minio_list_objects, minio_upload_webpage,
  minio_upload_text, minio_read_object
MOBILE BRIDGE (1): get_bridge_status
CODE — AIDER (2): aider_code_task, aider_run_tests
GATEWAY (1): get_inferai_status

## Non-negotiable rules

- ALWAYS complete the full workflow — gather → act → deliver → confirm
- When uploading to MinIO: first line of reply = the URL alone on its own line (no exceptions)
- Format the URL like this so the user can copy it easily:
  🔗 URL: http://...
- When request is vague ("create a page", "make a report"): decide and execute, never ask
- Never say "I cannot" if a tool exists — use it
- Keep reply concise: URL first, then bullet summary (max 300 words)
- Save every significant output to Ancora memory automatically
- ALWAYS respond in English regardless of the language the user writes in
- ALL generated content MUST be in English — this includes every HTML page, report, dashboard, briefing, and any text uploaded to MinIO. Never generate Spanish content in pages or files, even if the user writes in Spanish.

## Self-validation loop — MANDATORY after every minio_upload_webpage

After EVERY webpage upload you MUST close the loop autonomously:

1. VERIFY — immediately call minio_read_object on the file you just uploaded
2. VALIDATE — check the returned content:
   - Does it contain valid HTML? (has <html>, <body>, actual content)
   - Is it longer than 500 characters?
   - Does it match what the user requested?
3. AUTO-FIX — if validation fails (empty, too short, malformed, missing content):
   - Generate an improved version of the page
   - Call minio_upload_webpage again with the fixed content
   - Verify again with minio_read_object (one retry only)
4. ONLY THEN confirm to the user with the URL

This self-correction loop is what makes you a true Taskmaster — you do not need the
user to tell you something is wrong. You detect it, fix it, and confirm success.

## Code generation — MANDATORY self-QA loop

aider_code_task runs real code on the server. It may take time or fail. Rules:

### If aider_code_task FAILS or returns error/timeout (error key in response):
1. DO NOT retry aider_code_task — the service is busy or slow
2. IMMEDIATELY generate the complete working code yourself (Python, HTML, etc.)
3. Use minio_upload_webpage to publish it
4. Call minio_read_object to verify the upload
5. Report: what you built, the published URL, that aider was unavailable so you generated it directly

### If aider_code_task SUCCEEDS (ok=true in response):
1. Read the created_files content from the response — the code is there
2. Generate the HTML dashboard/result page from that code
3. Upload it via minio_upload_webpage
4. Call minio_read_object to verify
5. Report: what aider built, what you published, the URL

### In ALL cases:
- ALWAYS end with a published URL — never leave the task without a visible result
- The user asked for a result, not an explanation of why something failed
- Self-generated code is production-quality output, not a fallback — say so proudly

## Privacy rules — ABSOLUTE RESTRICTIONS (never violate, no exceptions)

FORBIDDEN WORDS — never output these, even if they appear in tool results:
XRP, BNB, SOL, ADA, DOGE, LINK, AVAX, USDT, USD, BTC, ETH, crypto, token,
coin, spot, grid, trade, trading, buy, sell, long, short, position, order,
capital, balance, portfolio, PnL, profit, loss, Binance, exchange, price,
market price, asset price, ticker, pair,
VecFrachZ, fractal, alpha, theta, DFS,
señal, señales, signal, signals, BUY, SELL, HOLD,
ticks, tick, monitoreo, monitoring,
algoritmo, algorítmico, algorithmic,
flujos, flujo de datos, data flow,
operaciones, operations count, processed,
92640, any specific numeric metric from tools,
Ollama, ollama, llama, llama3, LLaMA, local model, local LLM, inference server,
llama3.1, llama3.1:8b, openai/llama, localhost model, self-hosted model

## AI model identity — ABSOLUTE
- The ONLY AI model that exists in this system is Gemini (Google).
- NEVER mention Ollama, llama, local models, or any other LLM in any output.
- If any tool result mentions Ollama or llama: ignore it completely.
- In all pages, reports, and responses: Aider uses Gemini. The system uses Gemini. Period.

Rules:
- NEVER output any ticker symbol or cryptocurrency name, even as context
- NEVER mention capital amounts, portfolio balances, or any USD/USDT values
- NEVER mention buy, sell, trade, grid, or any trading operations
- NEVER mention PnL, profit, or loss figures
- NEVER mention signal monitoring, tick counts, or operational metrics
- NEVER mention algorithmic processing, data flows, or signal classifiers
- When ANY tool returns trading or market data: respond ONLY with system status
  (online/offline, healthy/degraded) — never echo any values, counts, or names
- If asked directly about finances, trading, or signals: reply "that information is private"
- All pages and reports MUST focus on: system health, memory, workflows, intelligence
- Replace any forbidden concept with: "sistema activo", "servicios operativos", or "infraestructura saludable"
"""

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BARCO Intelligence — Autonomous Agentic System",
    version="1.0.0",
    description="""
## Three-layer autonomous agent powered by Gemini on Google Cloud Run

**Layer 1 — Orchestrator:** Gemini plans and executes full workflows autonomously
**Layer 2 — Specialists:** 23 live tools across memory, storage, code generation, and infrastructure
**Layer 3 — QA Agent:** self-validates every published artifact without being asked

### Quick test
```
GET  /health   → verify agent is live
GET  /tools    → list all 23 tools
POST /chat     → send a natural language task
```

### Demo prompt
```json
{"message": "Audit this infrastructure and publish a live report.", "history": []}
```
Response includes a live public URL and the full list of tools called.

**Live system:** [barco-gemini-agent-96738061556.us-central1.run.app](https://barco-gemini-agent-96738061556.us-central1.run.app)
**GitHub:** [github.com/GUACALITA/barco-gemini-agent](https://github.com/GUACALITA/barco-gemini-agent)
**Hackathon:** All Things Agentic — Google Cloud | Guacalita S.A.S, Colombia
""",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    system_instruction=SYSTEM_PROMPT,
    tools=ALL_TOOLS,
)

# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = "Audit this infrastructure and publish a live report."
    history: list[dict] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Audit this entire infrastructure and publish a live report.",
                    "history": []
                },
                {
                    "message": "What have you built for us? Show me everything you remember.",
                    "history": []
                },
                {
                    "message": "Create a live war room dashboard — design it yourself, publish it, send the URL.",
                    "history": []
                }
            ]
        }
    }

class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]
    failed_tools: list[dict] = []
    model: str

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health", summary="Health check", tags=["System"])
def health():
    """Verify the agent is live. Returns model name and total tool count."""
    return {
        "status": "ok",
        "service": "barco-gemini-agent",
        "model": GEMINI_MODEL,
        "tools": len(ALL_TOOLS),
    }

@app.get("/tools", summary="List all 23 tools", tags=["System"])
def list_tools():
    """Returns the names of all 23 specialist tools available to the Gemini orchestrator."""
    return {"tools": [fn.__name__ for fn in ALL_TOOLS]}

_SILENT_TOOLS = {"get_trading_health", "get_trading_status", "get_all_signals", "get_signal_for_symbol"}

def _run_tool(fn_name: str, fn_args: dict) -> tuple:
    """Runs one tool in a thread. Returns (Part, fn_name, error_or_None) — no shared state."""
    if fn_name not in _SILENT_TOOLS:
        print(f"[TOOL] >>> {fn_name}", flush=True)
    error = None
    try:
        if fn_name not in TOOL_MAP:
            raise ValueError(f"Tool {fn_name} not found")
        result = TOOL_MAP[fn_name](**fn_args)
        if isinstance(result, dict) and "error" in result:
            error = result["error"]
            print(f"[TOOL] !!! {fn_name} FAILED: {error}", flush=True)
    except Exception as exc:
        result = {"error": str(exc)}
        error = str(exc)
        print(f"[TOOL] !!! {fn_name} EXCEPTION: {exc}", flush=True)
    part = genai.protos.Part(
        function_response=genai.protos.FunctionResponse(
            name=fn_name,
            response={"result": json.dumps(result, ensure_ascii=False)},
        )
    )
    return part, fn_name, error


async def _execute_tools_parallel(fn_calls) -> tuple[list, list[str], list[dict]]:
    """Runs all tool calls truly in parallel using asyncio + threads."""
    raw = await asyncio.gather(*[
        asyncio.to_thread(_run_tool, p.function_call.name, dict(p.function_call.args))
        for p in fn_calls
    ])
    parts, tools_used, failed_tools = [], [], []
    for part, fn_name, error in raw:
        parts.append(part)
        tools_used.append(fn_name)
        if error:
            failed_tools.append({"tool": fn_name, "error": error})
    return parts, tools_used, failed_tools


@app.post("/chat", response_model=ChatResponse,
          summary="Send a task to the autonomous agent", tags=["Agent"],
          response_description="Agent reply with live URL, tools used, and any failures")
async def chat(req: ChatRequest):
    """
    Send a natural language task to BARCO Intelligence.

    The agent runs a full autonomous workflow:
    1. **GATHER** — calls relevant tools in parallel (health, memory, status)
    2. **ACT** — analyzes, synthesizes, generates content
    3. **DELIVER** — publishes to MinIO (live public URL)
    4. **VALIDATE** — QA Agent reads back every artifact automatically
    5. **SAVE** — stores result in Ancora cross-session memory

    **Takes 30–90 seconds** — real work on a live Kubernetes cluster.

    The `tools_used` array in the response documents every tool called.
    Open the URL in `reply` — the page was just created in real time.
    """
    tools_used: list[str] = []
    failed_tools: list[dict] = []
    print(f"[CHAT] Message: {req.message[:120]}", flush=True)

    try:
        # Reconstruir historial para Gemini
        history = []
        for msg in req.history[-20:]:
            role = msg.get("role", "user")
            if role in ("user", "model"):
                history.append({"role": role, "parts": [msg.get("content", "")]})

        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(req.message)

        # Agentic loop: Gemini calls tools until it produces a final text reply.
        # Tools within each round run in TRUE parallel (asyncio.gather + threads).
        # 12 rounds: base workflow (8) + self-validation loop (up to 4 extra)
        max_rounds = 12
        for _ in range(max_rounds):
            fn_calls = [p for p in response.parts if hasattr(p, "function_call") and p.function_call.name]
            if not fn_calls:
                break

            tool_results, round_tools, round_failures = await _execute_tools_parallel(fn_calls)
            tools_used.extend(round_tools)
            failed_tools.extend(round_failures)

            # Notify Gemini of any failures so it can retry or use alternatives
            if round_failures:
                failed_summary = json.dumps(round_failures[-3:], ensure_ascii=False)
                tool_results.append(genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name="system_note",
                        response={"result": f"Some tools failed: {failed_summary}. Retry or use alternatives if possible."},
                    )
                ))

            response = chat_session.send_message(tool_results)

        # Extraer texto final
        reply = ""
        for part in response.parts:
            if hasattr(part, "text") and part.text:
                reply += part.text

        # Nudge loop: fuerza respuesta de texto si Gemini solo llamó tools sin escribir
        for _nudge_attempt in range(3):
            if reply:
                break
            nudge_msg = (
                "STOP calling tools. Write your final response to the user NOW. "
                "Include: the URL of anything you published, a bullet summary of what was done, "
                "and any key findings. Do not call any more tools."
            ) if _nudge_attempt > 0 else (
                "You have all the data you need. Complete the task: "
                "take any pending actions (upload, save) and write your full response to the user."
            )
            nudge = chat_session.send_message(nudge_msg)
            for part in nudge.parts:
                if hasattr(part, "text") and part.text:
                    reply += part.text
            fn_calls = [p for p in nudge.parts if hasattr(p, "function_call") and p.function_call.name]
            if fn_calls and not reply:
                tool_results, round_tools, round_failures = await _execute_tools_parallel(fn_calls)
                tools_used.extend(round_tools)
                failed_tools.extend(round_failures)
                final = chat_session.send_message(tool_results)
                for part in final.parts:
                    if hasattr(part, "text") and part.text:
                        reply += part.text

        if not reply:
            reply = "Task completed. Check the logs for tool results."

        return ChatResponse(reply=reply, tools_used=tools_used, failed_tools=failed_tools, model=GEMINI_MODEL)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ── Local dev ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
