# MongoDB on AWS — Demonstration App

An interactive demo suite for showcasing **MongoDB Atlas (on AWS)** capabilities.

- **Frontend:** Next.js 15 (App Router) + **LeafyGreen UI** (MongoDB's design system)
- **Backend:** Python FastAPI (async PyMongo)
- **Database:** MongoDB Atlas
- **Embeddings:** Voyage AI · **Chat/agent (later features):** Claude on AWS Bedrock

## Status

| # | Feature | Route | State |
|---|---------|-------|-------|
| 1 | **Search: full-text, vector & hybrid** (RRF) over `embedded_movies` | `/search` | ✅ Built & tested |
| 2 | **Agentic memory** (LangGraph + Claude/Bedrock, MongoDB memory) | `/memory` | ✅ Built & tested |
| 3 | **Deploy MCP server on Bedrock AgentCore** (guided walkthrough) | `/mcp-deploy` | ✅ Built & tested |
| 4 | **Auto-embedding vector index** (Atlas-managed Voyage) | `/autoembed` | ✅ Built & tested |
| 5 | **Stream processing ↔ AWS Kinesis** (guided + simulated flow) | `/stream` | ✅ Built & tested |

All five features are implemented with real backend logic following the source
references. Features 3 & 5 use **guided, simulated** flows (real commands/pipelines,
no live AWS provisioning) so they are safe and repeatable in front of an audience.

## Repository layout

```
.
├── amplify.yml             # Amplify Hosting build spec (frontend only)
├── .env.example            # all required configuration (copy to .env)
├── backend/                # FastAPI service
│   ├── Dockerfile          # backend container image (Lambda + Web Adapter)
│   ├── app/
│   │   ├── main.py         # app factory, CORS, /health
│   │   ├── config.py       # pydantic-settings (reads ../.env)
│   │   ├── db.py           # async Atlas client lifecycle
│   │   ├── routers/search.py
│   │   ├── services/{search_service,embeddings}.py
│   │   └── models/search.py
│   ├── scripts/seed_search_indexes.py
│   └── tests/              # pytest (unit + gated live integration)
└── frontend/               # Next.js app
    ├── app/{layout,page}.tsx, app/search/page.tsx
    ├── components/, lib/
    └── __tests__/          # Jest + React Testing Library
```

## Prerequisites

- **Node.js 18+** (built with 22) and **Python 3.13** (3.11–3.13 supported; 3.14 has
  ecosystem wheel gaps — use 3.13).
- A **MongoDB Atlas** cluster on AWS with the **`sample_mflix`** sample dataset loaded
  (provides `embedded_movies`). Automated embedding (Feature 4) requires an Atlas tier
  that supports Vector Search auto-embedding.
- A **Voyage AI** API key (https://www.voyageai.com/) — used by Features 1, 2, 4.
- **AWS Bedrock** access in your region with the Claude model enabled (Feature 2 agent).
  Leave `AWS_ACCESS_KEY_ID`/`SECRET` blank to use the default credential chain (e.g. an
  IAM role on Amplify), or set them explicitly for local dev.

## Setup

### 1. Configure environment
```bash
cp .env.example .env
# Fill in MONGODB_URI, VOYAGE_API_KEY, and (for later features) AWS_* values.
```

### 2. Backend
```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Seed Voyage embeddings + Atlas search indexes (one-time)
`embedded_movies` ships with a 1536-dim OpenAI embedding. Because we use **Voyage**, the
seed script computes a matching `plot_embedding_voyage` (1024-dim) field and builds both
the full-text and vector indexes:
```bash
cd backend && source .venv/bin/activate
python -m scripts.seed_search_indexes            # embeddings + both indexes
# Faster trial run on a subset:
python -m scripts.seed_search_indexes --limit 500
```
> Atlas builds search indexes asynchronously — give them a minute to become queryable.

### 4. Run the backend
```bash
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs   ·   Health: http://localhost:8000/health
```

### 5. Run the frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000  →  /search
```

## Feature 1 — how the search demo works

`GET /api/search/compare?q=...` runs **all three** strategies for one query so the UI can
show them side by side:

- **Full-text** — Atlas Search `$search` (text operator over title/plot/genres/cast).
- **Vector** — `$vectorSearch` over the Voyage embedding; the query is embedded with Voyage.
- **Hybrid** — **Reciprocal Rank Fusion** of the two lists, computed in the service so each
  card can display its contributing `text #` / `vector #` ranks and fused RRF score.

Curated example queries (`GET /api/search/examples`) are chosen to make the differences
obvious on screen — e.g. *"loneliness of space exploration"* (vector shines) vs.
*"The Godfather"* (full-text wins on exact titles).

## Feature 2 — agentic memory (LangGraph + MongoDB)

A LangGraph `StateGraph` (`recall → agent → memorize`) backed by MongoDB:

- **Short-term** thread memory is checkpointed by the LangGraph **MongoDBSaver**, keyed by
  `thread_id` (conversation continuity within a thread).
- **Long-term** memory: durable facts about the user are embedded with Voyage and stored in
  `agentic_memory.long_term_memories`, then **recalled across threads** by semantic similarity.
- The LLM is **Claude via AWS Bedrock** (`langchain-aws`).

The `/memory` page has a guided 3-step script that proves cross-thread recall (state a fact in
thread A, switch to thread B, watch the agent recall it). `POST /api/memory/chat` returns the
reply plus which memories were `recalled` and `saved` this turn.

## Feature 3 — deploy MCP server on Bedrock AgentCore (guided)

`/mcp-deploy` renders the real steps from
[`mongodb-mcp-server/deploy/aws`](https://github.com/mongodb-js/mongodb-mcp-server/tree/main/deploy/aws)
as copy-paste commands parameterised with **your** account ID / region / repo. Each step has a
**Simulate** button that returns realistic output (`POST /api/mcp-deploy/simulate`) — **no real
AWS calls**, so it never fails mid-demo. Covers ECR repo → auth → ARM64 build → push → create
AgentCore runtime (with the required `MDB_MCP_*` env) → invoke (`tools/list`) → CloudWatch logs.

## Feature 4 — auto-embedding vector index

`/autoembed` demonstrates **Atlas-managed embeddings**. The index uses
`{ "type": "autoEmbed", "path": "description", "modality": "text", "model": "voyage-4" }` — you store **plain text only**
and query with a **text string** (`$vectorSearch.query`); Atlas embeds documents and queries for
you. A curated 20-destination dataset gives visibly-distinct semantic results. The page lets you
ingest + create the index, poll until `READY`, then search by meaning.

## Feature 5 — stream processing ↔ AWS Kinesis (guided)

`/stream` shows both directions of Atlas Stream Processing with Kinesis: **Kinesis → validate →
`$merge` to Atlas**, and **Atlas change stream → filter → `$emit` to Kinesis**. It displays the
real connection-registry entries, the stream-processor pipeline, and the `sp.*` management
commands, then **streams synthetic IoT telemetry** through the pipeline so the audience watches
each record route to a sink or the dead-letter queue (`POST /api/stream/simulate`, deterministic).

## Testing

```bash
# Backend — unit tests (hermetic; live integration auto-skips without creds)
cd backend && source .venv/bin/activate && python -m pytest -q

# Backend — live integration (requires real creds + seeded indexes)
MONGODB_URI=... VOYAGE_API_KEY=... python -m pytest tests/test_integration_live.py -v

# Frontend — component + API-client tests
cd frontend && npm test

# Frontend — production build (also a smoke test for SSR/LeafyGreen)
npm run build
```

## Deployment to AWS

The app deploys as **two services** that share the same backends (Atlas, Bedrock, Voyage):

```
            ┌───────────────────────┐        ┌────────────────────────────┐
 Browser ──▶│  Next.js frontend     │ ─API─▶ │  FastAPI backend           │
            │  AWS Amplify Hosting   │        │  AWS Lambda (container +    │
            │                        │        │  Web Adapter, Function URL) │
            └───────────────────────┘        └─────────────┬──────────────┘
                                                            │
                                        MongoDB Atlas · AWS Bedrock · Voyage AI
```

Amplify Hosting natively builds and serves the **Next.js** app. The **FastAPI** backend runs on
**AWS Lambda** as a container image, fronted by a **Lambda Function URL**;
`NEXT_PUBLIC_API_BASE_URL` points the frontend at that URL. `amplify.yml` therefore targets only
`frontend/`, and `backend/Dockerfile` packages the backend.

> **Why a container + Lambda Web Adapter (not Mangum)?** The
> [AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter) (baked into
> `backend/Dockerfile`) runs uvicorn unchanged, so the app's async Mongo lifespan and async code
> work exactly as they do locally — no handler rewrite, and none of the event-loop pitfalls of
> running an async Mongo driver under Mangum.

### A. Deploy the backend → AWS Lambda (container image)

1. Build and push the image to Amazon ECR (arm64 / Graviton — cheaper, and matches Apple-silicon
   build hosts; run from the repo root):
   ```bash
   export AWS_REGION=us-east-1
   export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   export ECR=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mongodb-aws-backend

   aws ecr create-repository --repository-name mongodb-aws-backend --region $AWS_REGION
   aws ecr get-login-password --region $AWS_REGION \
     | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
   docker build --platform linux/arm64 -t $ECR:latest backend/
   docker push $ECR:latest
   ```
2. Create the Lambda function from the image (needs an execution role with the basic Lambda logs
   policy **plus** `bedrock:InvokeModel`):
   ```bash
   aws lambda create-function \
     --function-name mongodb-aws-backend \
     --package-type Image \
     --code ImageUri=$ECR:latest \
     --role arn:aws:iam::$ACCOUNT_ID:role/<lambda-exec-role> \
     --architectures arm64 \
     --timeout 120 --memory-size 1536 \
     --environment "Variables={MONGODB_URI=...,MONGODB_DB=sample_mflix,VOYAGE_API_KEY=...,BEDROCK_CHAT_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0,AUTOEMBED_MODEL=voyage-4,CORS_ORIGINS=*}" \
     --region $AWS_REGION
   ```
3. Add a public **Function URL** (HTTPS endpoint the frontend calls):
   ```bash
   aws lambda create-function-url-config \
     --function-name mongodb-aws-backend --auth-type NONE --region $AWS_REGION
   aws lambda add-permission \
     --function-name mongodb-aws-backend --statement-id public-url \
     --action lambda:InvokeFunctionUrl --principal '*' \
     --function-url-auth-type NONE --region $AWS_REGION
   ```
   The first command returns a `FunctionUrl` like `https://<id>.lambda-url.us-east-1.on.aws/`.

**Notes**
- **Bedrock auth:** grant the **execution role** `bedrock:InvokeModel` and **do not** set
  `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` in the Lambda env — Lambda
  injects its own role credentials, and setting them would override the role.
- **Don't set Function URL CORS** — the FastAPI app already sends CORS headers (via `CORS_ORIGINS`);
  configuring CORS on the Function URL too would duplicate the headers and break the browser.
- **Cold starts:** the image is large (LangChain/LangGraph), so the first call is slow. Use
  **provisioned concurrency** for a snappy live demo.
- **Redeploy after a new image:**
  `aws lambda update-function-code --function-name mongodb-aws-backend --image-uri $ECR:latest`.

> **Atlas network access:** Lambda egresses from dynamic AWS IPs. For a demo, add `0.0.0.0/0` to
> Atlas **Network Access**. For a fixed egress IP, run the function in a **VPC** with a NAT gateway
> and allow-list that IP.

### B. Deploy the frontend → AWS Amplify Hosting

1. Push this repo to GitHub / GitLab / Bitbucket / CodeCommit.
2. **Amplify console → Create new app → Connect** your repository and branch.
3. Amplify reads `amplify.yml` and detects the monorepo app root **`frontend`** — accept it.
4. Add an **environment variable** (use the Function URL from step A, with **no** trailing slash):
   ```
   NEXT_PUBLIC_API_BASE_URL = https://<id>.lambda-url.us-east-1.on.aws
   ```
   > `NEXT_PUBLIC_*` values are inlined into the client bundle at **build time** — set this
   > **before** the build and **redeploy** whenever the backend URL changes.
5. **Save and deploy.** Amplify serves the app at `https://<branch>.<app-id>.amplifyapp.com`.

### C. Connect the two (CORS)

Point the backend's `CORS_ORIGINS` at the Amplify domain and update the Lambda function:
```bash
aws lambda update-function-configuration \
  --function-name mongodb-aws-backend \
  --environment "Variables={...,CORS_ORIGINS=https://<branch>.<app-id>.amplifyapp.com}" \
  --region $AWS_REGION
```
(Repeat the full `Variables={...}` set — `update-function-configuration` replaces the whole map.)

### D. One-time data setup

Seed the search data against the same Atlas cluster (run locally or as a one-off task), then
create the auto-embedding index from the UI:
```bash
cd backend && source .venv/bin/activate && python -m scripts.seed_search_indexes
```
Then open `/autoembed` and click **Ingest + create index** (Feature 4).

### Deployment checklist

- [ ] **Atlas Network Access** allows the backend (e.g. `0.0.0.0/0` for a demo).
- [ ] **Atlas sample data** (`sample_mflix`) loaded; search indexes seeded (step D).
- [ ] **Bedrock model access** enabled for `BEDROCK_CHAT_MODEL_ID` in `AWS_REGION`, and the
      Lambda **execution role** has `bedrock:InvokeModel` (Feature 2).
- [ ] **Auto-embed model** (`AUTOEMBED_MODEL`) is one Atlas supports: `voyage-4`,
      `voyage-4-large`, `voyage-4-lite`, `voyage-code-3` (Feature 4).
- [ ] Lambda env vars set; `CORS_ORIGINS` = the Amplify URL; AWS key vars **left unset** (role only).
- [ ] Frontend `NEXT_PUBLIC_API_BASE_URL` = the Lambda **Function URL**, and **redeployed** after setting it.
- [ ] Never commit `.env` — set all secrets in the Lambda / Amplify consoles.

## Design decisions

- **LeafyGreen UI** over a hand-rolled theme — it *is* mongodb.design, so the demo looks
  authentically MongoDB.
- **Voyage `plot_embedding_voyage` field** so query and document embeddings use the same
  model/dimensionality (the built-in `plot_embedding` is a different model).
- **RRF in Python** (vs. a server-side `$rankFusion` stage) to keep per-method ranks
  visible — the side-by-side ranking difference is the point of the demo.
- **Graceful degradation** — the app boots and serves docs/UI even without creds; endpoints
  return clear `503`s telling you which env var is missing, so a half-configured demo never
  crashes mysteriously.
