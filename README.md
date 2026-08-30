# BARCO Intelligence — Autonomous Agentic System

**Hackathon:** All Things Agentic — Google Cloud
**Track:** Taskmaster + Startup Excellence
**Company:** Guacalita S.A.S, Colombia
**Live agent:** https://barco-gemini-agent-96738061556.us-central1.run.app
**Demo video:** https://youtu.be/x5O5jLixT6w

---

## Mandatory Technologies

| Requirement | Implementation |
|---|---|
| **Gemini 3.5 or newer** | `gemini-3.5-flash` via Gemini API |
| **Google Agent Framework** | **Google GenAI SDK** (`google-generativeai==0.8.3`) — function calling, parallel tool orchestration, 12-round agentic loop |
| **Google Cloud Infrastructure** | **Google Cloud Run** — serverless container hosting the FastAPI orchestrator |
| **Additional Google AI Model** | **Gemma** (on-device via `flutter_gemma` in Flutter app) — offline fallback, zero downtime |

---

## Bring Your Own Friction (BYOF)

**The friction:** Managing 26 live microservices on Kubernetes required 4–6 manual API calls in the correct order for every status report, published page, or diagnostic script. There was no intelligence layer. Every workflow was human-driven. Every result was ephemeral — no memory, no persistence, no validation.

**The solution:** BARCO Intelligence eliminates every manual step. One message. The agent gathers live data from all 26 services, writes and executes real Python on the production server, publishes validated artifacts to public URLs, and saves the result to cross-session persistent memory — autonomously, end-to-end, with a mandatory QA gate after every action.

This is not a hypothetical use case. It is the system we built to manage our own infrastructure. The 26 Kubernetes pods visible in the demo are real, live, and serving production traffic.

---

## What Is This?

**BARCO Intelligence** is a three-layer autonomous agent that takes a single natural language command and executes a complete workflow — gathering live intelligence from 23 real production tools, writing and running code via Aider (Gemini-powered, real Linux server), publishing artifacts to live public URLs, self-validating every output via a mandatory QA loop, and committing results to persistent cross-session memory — with zero human confirmation steps between intent and result.

One message. Full agentic loop. The system never goes dark: when offline, Gemma runs on-device via flutter_gemma, maintaining full conversational capability until the network returns.

---

## Architecture — 3 Layers

| Layer | Component | What It Does |
|---|---|---|
| **Orchestrator** | Gemini on Cloud Run | Receives natural language, plans workflow, calls up to 5 tools simultaneously, runs up to 12 agentic rounds |
| **Specialists** | 23 tools across 6 groups | Live data, semantic memory, agent memory, object storage, code generation, infrastructure health |
| **QA Agent** | Self-validation loop in system prompt | After every `minio_upload_webpage`, reads the artifact back, validates structure and content, auto-regenerates if broken — no user trigger |

```
┌─────────────────────────────────────────────────────────────┐
│  AncloFlutter — Flutter app (Android + Web)                 │
│                                                             │
│  Online  → Gemini via Cloud Run (23 live tools)             │
│  Offline → Gemma on-device (flutter_gemma, zero downtime)   │
└──────────────────┬──────────────────────────────────────────┘
                   │  HTTPS
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Google Cloud Run — barco-gemini-agent                      │
│                                                             │
│  Orchestrator: Gemini (gemini-3.5-flash) via GenAI SDK      │
│    → agentic loop: up to 12 rounds                          │
│    → parallel tool execution: asyncio.gather + threads      │
│    → gather → act → deliver → validate → save               │
│                                                             │
│  QA Agent: minio_read_object fires automatically            │
│  after every upload — zero user trigger                     │
└──────────────────┬──────────────────────────────────────────┘
                   │  HTTP
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Production VPS — Kubernetes (k3s)                          │
│                                                             │
│  Semantic Memory   Milvus + fastembed (1,068+ vectors)      │
│  Agent Memory      Ancora — cross-session persistence       │
│  Object Storage    MinIO — live public URLs                 │
│  Code Execution    Aider (Gemini-powered) on real server    │
│  Mobile Bridge     Push → AncloFlutter devices              │
│  AI Gateway        InferAI                                  │
│  + Kafka, Redis, 20+ additional microservices               │
└─────────────────────────────────────────────────────────────┘
```

> **Interactive diagram:** Open `architecture.html` directly in any browser for a full visual representation with component details.

---

## Repository Structure

```
barco-gemini-agent/
├── main.py              FastAPI app — agentic loop, system prompt, parallel tool orchestration
├── tools.py             23 tool implementations — one Python function per tool
├── Dockerfile           Cloud Run container (python:3.11-slim, uvicorn)
├── requirements.txt     fastapi, uvicorn, google-generativeai, boto3, requests, pydantic
├── .env.example         Required environment variables
├── architecture.html    Interactive architecture diagram — open directly in browser
├── .gitignore
└── README.md
```

---

## 23 Tools in 6 Groups

### 1. System Intelligence (5)
| Tool | Endpoint | Description |
|---|---|---|
| `get_trading_status` | `:30835/api/status` | Live system operational status |
| `get_trading_health` | `:30835/health` | Infrastructure health check |
| `get_all_signals` | `:30818/signals` | Real-time classifier status |
| `get_signal_for_symbol` | `:30818/price` | Status for a specific data feed |
| `get_vecfrachz_health` | `:30818/health` | Signal processor health |

### 2. Memory & Orchestration (5)
| Tool | Endpoint | Description |
|---|---|---|
| `search_memory` | `:8901/search` | Semantic search — Milvus, 1,068+ vectors, fastembed 384-dim |
| `get_memory_health` | `:8901/health` | Memory system status |
| `run_market_analysis` | `:30814/run-workflow` | Full analysis via SwarmOrchestrator |
| `get_swarm_health` | `:30814/health` | SwarmOrchestrator agent registry |
| `route_query` | `:30816/route` | Intent classifier — routes to BARCO context |

### 3. Agent Memory — Ancora (4)
| Tool | Endpoint | Description |
|---|---|---|
| `ancora_get_context` | `:31437/context` | Full agent context and stored knowledge |
| `ancora_get_recent` | `:31437/observations/recent` | Recent observations — cross-session |
| `ancora_search` | `:31437/search` | Search agent memory by text |
| `ancora_add_observation` | `:31437/observations` | Write fact or event to persistent memory |

### 4. Object Storage — MinIO (5)
| Tool | Description |
|---|---|
| `minio_list_buckets` | List all storage buckets |
| `minio_list_objects` | List files in a bucket |
| `minio_upload_webpage` | Publish HTML to a live public URL |
| `minio_upload_text` | Upload text, JSON, or scripts |
| `minio_read_object` | Read file content — primary QA validation tool |

### 5. Mobile Bridge (1)
| Tool | Endpoint | Description |
|---|---|---|
| `get_bridge_status` | `:31900/health` | Mobile bridge and connected device registry |

### 6. Code Generation — Aider (2)
| Tool | Endpoint | Description |
|---|---|---|
| `aider_code_task` | `:30808/code-task` | Write and run code on the live production server (Gemini-powered) |
| `aider_run_tests` | `:30808/run-tests` | Run test suite, return live terminal output |

### AI Gateway (1)
| Tool | Endpoint | Description |
|---|---|---|
| `get_inferai_status` | `:30815/health` | AI gateway status |

---

## How Parallel Execution Works

Gemini's function calling API can return multiple tool calls in a single response. The FastAPI backend resolves them concurrently using the **Google GenAI SDK**:

```python
# main.py — _execute_tools_parallel()
raw = await asyncio.gather(*[
    asyncio.to_thread(_run_tool, p.function_call.name, dict(p.function_call.args))
    for p in fn_calls
])
```

`asyncio.gather` + `asyncio.to_thread` means all tools in a single Gemini round execute simultaneously in separate threads — not sequentially. This is observable in Cloud Logging: 5 `[TOOL]` lines appear within milliseconds of each other, not one at a time.

---

## QA Self-Validation Loop

After **every** `minio_upload_webpage`, the agent activates a validation cycle with zero user input:

```
1. minio_upload_webpage  → publishes HTML artifact
2. minio_read_object     → reads back the published file (unprompted)
3. VALIDATE              → real HTML? content complete? length > 500 chars?
4. AUTO-FIX              → if broken: regenerate + re-upload (one retry)
5. CONFIRM               → only then returns the public URL
```

This is not a code wrapper or callback. It is a behavioral constraint in the system prompt — Gemini internalizes it and executes it as part of its own reasoning chain. Observable in Cloud Logging as `minio_upload_webpage` immediately followed by `minio_read_object` in every session.

---

## Implementation Insights

### 1. QA Is Emergent, Not Hardcoded
The validation loop is a prompt rule: "After every minio_upload_webpage, you MUST call minio_read_object." Gemini treats this as an unconditional obligation. The validation logic lives in the model's reasoning, not in a post-upload hook — which means the agent applies judgment about what "valid" means, not just a character count check.

### 2. True Parallel Orchestration via Native Function Calling
When Gemini is not constrained by sequential dependencies, it returns multiple function calls in one response. The first round of a briefing task typically fires 5 tools simultaneously: health checks, memory search, context retrieval, and routing — all in a single Gemini API response resolved concurrently by the backend.

### 3. Privacy Governance at the Model Layer
Financial figures, operational metrics, and account data are redacted from all agent responses by a rule in the system prompt — not a regex filter or post-processing scrubber. The model decides what to surface. This is the correct architecture for compliance environments where AI response leakage is a regulatory risk.

### 4. Cross-Session Memory Without Infrastructure Changes
Ancora stores observations automatically after every completed task. A new session with an empty `history: []` payload loads those observations via `ancora_get_context` and returns exact URLs and details from previous sessions. Two tools replace a full event-sourcing or database schema implementation.

### 5. Dual AI, Zero Downtime
Most agent systems go dark when the API is unreachable. AncloFlutter runs Gemma on-device via flutter_gemma when offline — same UI, same conversation flow, local SQLite memory and RAG. No single point of failure at the AI layer.

---

## Design Decisions

### Why Google GenAI SDK?
The `google-generativeai` SDK provides native function calling with structured `FunctionDeclaration` objects — no JSON schema workarounds. Tool call batching (multiple calls per Gemini response) is a first-class feature that enables true parallel execution. The SDK's streaming API makes 30–90 second agentic loops feasible in a Cloud Run environment with 300-second timeout.

### Why Milvus, Not pgvector?
Milvus is purpose-built for ANN search at scale. The 1,068 vectors currently indexed are a starting point — the architecture is designed to grow to millions of embeddings (system events, agent memories, historical data) without re-engineering the query layer. Milvus also supports multiple index types and filtering on metadata alongside vectors.

### Why Ancora for Agent Memory?
Ancora gives the agent a structured memory interface via four operations (get context, get recent, search, add) that map directly to tool calls. The agent does not manage a database — it uses a memory API. This keeps agent code decoupled from storage implementation.

### Why Cloud Run, Not a Persistent VM?
Cloud Run is correct for agentic backends with long idle periods and compute-heavy bursts (12-round agentic loops). Scales to zero when idle, scales up instantly, provides built-in HTTPS and Google Cloud Logging — the full audit trail for every tool call is included infrastructure, not custom code.

### Why Aider on a Real Server?
When the agent writes a health monitoring script, it runs against real endpoints. When it generates a dashboard, the data is live. The output in the agent's response is real terminal output — not mocked, not sandboxed. The tradeoff is intentional: production risk in exchange for production-grade results.

---

## Security & Governance

| Layer | Control |
|---|---|
| **Transport** | HTTPS on all Cloud Run endpoints (Google-managed TLS) |
| **Access** | Cloud Run IAM — unauthenticated access on public demo endpoints only |
| **Data at rest** | AES-256 encryption in Flutter app (Hive) |
| **Financial data** | Redacted from all responses via system prompt rule — not post-processing |
| **Audit trail** | Full tool call log in Google Cloud Logging — every `[TOOL] >>> name` timestamped |
| **Artifact integrity** | QA self-validation gate — no unvalidated artifact reaches the user |

---

## Reproducible Testing

The live agent is deployed and publicly accessible. **No API key required from the judge.**

### 0. Interactive API docs (fastest way to test)

Open either URL in a browser — fully interactive, no curl required:

- **Swagger UI:** https://barco-gemini-agent-96738061556.us-central1.run.app/docs

The `/docs` page lists all endpoints with example payloads pre-filled. Click **POST /chat → Try it out → Execute** and the agent runs live. The `tools_used` array in the response documents every tool called. `reply` contains the live public URL of the published artifact.

> **Note:** `/chat` takes 30–90 seconds — the agent is doing real work on a live Kubernetes cluster, not returning cached results.

### Real execution example (recorded 2026-08-30)

Request:
```json
{"message": "Create a beautiful status dashboard for this infrastructure.", "history": []}
```

Response:
```json
{
  "reply": "🔗 URL: http://207.180.253.38:30091/sitios-web/dashboard-status.html\n\nModern Slate-950 dark mode dashboard powered by Tailwind CSS...",
  "tools_used": [
    "get_memory_health",
    "get_swarm_health",
    "get_inferai_status",
    "get_bridge_status",
    "minio_upload_webpage",
    "minio_read_object",
    "ancora_add_observation"
  ],
  "failed_tools": [],
  "model": "gemini-3.5-flash"
}
```

Key observations from this run:
- `minio_read_object` fired **automatically** after `minio_upload_webpage` — QA self-validation with zero user input
- `failed_tools: []` — zero failures across all 7 tools
- `server: Google Frontend` in response headers confirms Google Cloud Run execution
- `x-cloud-trace-context` header confirms Cloud Logging traceability

### 1. Verify the agent is live

```bash
curl https://barco-gemini-agent-96738061556.us-central1.run.app/health
```

Expected:
```json
{"status":"ok","service":"barco-gemini-agent","model":"gemini-3.5-flash","tools":23}
```

### 2. List all 23 tools

```bash
curl https://barco-gemini-agent-96738061556.us-central1.run.app/tools
```

### 3. Demo A — Autonomous investigation + live publish

```bash
curl -X POST https://barco-gemini-agent-96738061556.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Audit this entire infrastructure right now. Check every service, compare against everything you remember, find what changed, and publish a live incident report.",
    "history": []
  }'
```

**What to observe:** The response JSON contains `tools_used` — you will see 8–15 different tools called in one request. The `reply` field contains a live public URL. Open it — the page exists and was just created.

Expected `tools_used` includes: `get_memory_health`, `get_swarm_health`, `get_bridge_status`, `search_memory`, `ancora_get_recent`, `ancora_search`, `minio_upload_webpage`, `minio_read_object` (QA, automatic), `ancora_add_observation`.

### 4. Demo B — Cross-session persistent memory

```bash
# First call — build something:
curl -X POST https://barco-gemini-agent-96738061556.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Publish a brief status page for BARCO Intelligence and save it to memory.", "history": []}'

# Second call — completely new session, empty history:
curl -X POST https://barco-gemini-agent-96738061556.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What have you built for us? Show me everything you remember.", "history": []}'
```

**What to observe:** The second call returns exact URLs and details from the first call with `history: []` — no conversation context passed. This is Ancora, not conversation history.

### 5. Demo C — Creative autonomous page creation

```bash
curl -X POST https://barco-gemini-agent-96738061556.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a live war room dashboard for this infrastructure — real data, real status, real memory — design it yourself, make it beautiful, publish it and send the URL.",
    "history": []
  }'
```

**What to observe:** The agent decides structure, content, and design with no instructions. The reply starts with a live public URL. Open it — the dashboard reflects real system data at the time of creation.

### 6. Observe tool calls in real time

```
Google Cloud Console → Cloud Run → barco-gemini-agent → Logs → Stream logs
```

Each tool call: `[TOOL] >>> tool_name`
Parallel execution: multiple `[TOOL]` lines with timestamps within milliseconds of each other.
QA pattern: `minio_upload_webpage` always followed by `minio_read_object` in the same session.

### PowerShell (Windows)

```powershell
$body = @{
    message = "Audit this entire infrastructure right now. Check every service, compare against everything you remember, find what changed, and publish a live incident report."
    history = @()
} | ConvertTo-Json -Depth 3

Invoke-RestMethod `
    -Uri "https://barco-gemini-agent-96738061556.us-central1.run.app/chat" `
    -Method POST -ContentType "application/json" `
    -Body $body -TimeoutSec 270
```

> **Note:** Requests take 30–90 seconds. The agent is doing real work against a live Kubernetes cluster — not returning cached results. The `tools_used` array in the response documents every tool called.

---

## What the Video Does Not Show

**Parallel execution internals.** The video shows results. It cannot show that 5 tools were called simultaneously in one Gemini response. Check `tools_used` in any API response — then check Cloud Logging timestamps. You will see them land within milliseconds of each other.

**Cross-session memory.** Run Demo B above. The second call returns exact URLs from the first call with `history: []`. This is Ancora — not conversation history, not context window.

**QA repairing a broken artifact.** If the first upload is under 500 characters or missing HTML structure, the agent regenerates it automatically. The user never sees the broken version. Check logs for consecutive `minio_upload_webpage` → `minio_read_object` → `minio_upload_webpage` sequences.

**Code running on a real server.** `aider_code_task` sends the task to a real production server (Kubernetes cluster, live services). The terminal output in the agent's response is real — not mocked.

**Offline mode.** Disconnect the network on the Flutter app. Gemma continues answering using local memory. Reconnect — switches back to Gemini automatically.

---

## Local Development

```bash
git clone https://github.com/guacalita/barco-gemini-agent
cd barco-gemini-agent
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY in .env
uvicorn main:app --host 0.0.0.0 --port 8080
```

The agent will start but tools pointing to production services will be unreachable from localhost. The Gemini orchestration, system prompt, and agentic loop are fully testable locally with any tools that respond.

---

## Deploy Your Own Instance to Cloud Run

```bash
gcloud run deploy barco-gemini-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=your_key,GEMINI_MODEL=gemini-1.5-flash" \
  --memory 512Mi \
  --timeout 300
```

Point the tool URLs in `tools.py` to your own services, or swap the tool implementations entirely — the orchestration layer in `main.py` is service-agnostic.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-3.5-flash` | Gemini model name |
| `PORT` | No | `8080` | Server port (Cloud Run sets this automatically) |

---

## Google AI Models in This System

| Model | Where | Role |
|---|---|---|
| **Gemini** (gemini-3.5-flash) | Google Cloud Run | Orchestrator — planning, parallel tool calling, 12-round agentic loop via Google GenAI SDK |
| **Gemma** | Flutter app (on-device) | Offline fallback — local inference via flutter_gemma, zero downtime |

Two Google AI models. One user message. The system never goes dark.

---

## Bonus Contributions

| Contribution | Status |
|---|---|
| LinkedIn post with `#AllThingsAgenticHackathon` | Published |
| Gemma integration (flutter_gemma on-device) | Active in Flutter app |

---

## Company

**Guacalita S.A.S** — Colombia
Contact: j0lug0b4@gmail.com

*This project was built during the All Things Agentic Hackathon (August 3–31, 2026) for the purpose of entering this contest.*
