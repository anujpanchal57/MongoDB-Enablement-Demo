// Typed client for the FastAPI backend. The base URL comes from the
// NEXT_PUBLIC_API_BASE_URL env var (see .env.example).

import type {
  AutoEmbedDataset,
  AutoEmbedSearchResponse,
  AutoEmbedSetup,
  AutoEmbedStatus,
  ChatResponse,
  CompareResponse,
  DeployConfig,
  DeploySteps,
  ExampleQuery,
  MemoryDemoScript,
  MemoryList,
  SearchMode,
  SearchResponse,
  SimulateStepResult,
  StreamScenarios,
  StreamSimulation,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<{
  status: string;
  mongodb_configured: boolean;
  mongodb_reachable: boolean;
  voyage_configured: boolean;
}> {
  return handle(await fetch(`${BASE_URL}/health`, { cache: 'no-store' }));
}

export async function getExamples(): Promise<ExampleQuery[]> {
  const data = await handle<{ examples: ExampleQuery[] }>(
    await fetch(`${BASE_URL}/api/search/examples`, { cache: 'no-store' }),
  );
  return data.examples;
}

export async function runSearch(
  query: string,
  mode: SearchMode,
  limit = 10,
): Promise<SearchResponse> {
  return handle(
    await fetch(`${BASE_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, mode, limit }),
    }),
  );
}

export async function compareSearch(query: string, limit = 10): Promise<CompareResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return handle(
    await fetch(`${BASE_URL}/api/search/compare?${params.toString()}`, { cache: 'no-store' }),
  );
}

// ---- Feature 4: auto-embedding ----
export async function getAutoEmbedDataset(): Promise<AutoEmbedDataset> {
  return handle(await fetch(`${BASE_URL}/api/autoembed/dataset`, { cache: 'no-store' }));
}

export async function autoEmbedSetup(): Promise<AutoEmbedSetup> {
  return handle(await fetch(`${BASE_URL}/api/autoembed/setup`, { method: 'POST' }));
}

export async function getAutoEmbedStatus(): Promise<AutoEmbedStatus> {
  return handle(await fetch(`${BASE_URL}/api/autoembed/status`, { cache: 'no-store' }));
}

export async function autoEmbedSearch(query: string, limit = 8): Promise<AutoEmbedSearchResponse> {
  return handle(
    await fetch(`${BASE_URL}/api/autoembed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit }),
    }),
  );
}

// ---- Feature 2: agentic memory ----
export async function memoryChat(
  message: string,
  threadId: string,
  userId: string,
): Promise<ChatResponse> {
  return handle(
    await fetch(`${BASE_URL}/api/memory/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, thread_id: threadId, user_id: userId }),
    }),
  );
}

export async function getMemories(userId: string): Promise<MemoryList> {
  const params = new URLSearchParams({ user_id: userId });
  return handle(await fetch(`${BASE_URL}/api/memory/list?${params}`, { cache: 'no-store' }));
}

export async function clearMemories(userId: string): Promise<{ deleted: number }> {
  const params = new URLSearchParams({ user_id: userId });
  return handle(await fetch(`${BASE_URL}/api/memory/clear?${params}`, { method: 'POST' }));
}

export async function getMemoryDemoScript(): Promise<MemoryDemoScript> {
  return handle(await fetch(`${BASE_URL}/api/memory/demo-script`, { cache: 'no-store' }));
}

// ---- Feature 3: MCP on AgentCore ----
export async function getDeploySteps(config?: DeployConfig): Promise<DeploySteps> {
  if (!config) {
    return handle(await fetch(`${BASE_URL}/api/mcp-deploy/steps`, { cache: 'no-store' }));
  }
  return handle(
    await fetch(`${BASE_URL}/api/mcp-deploy/steps`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }),
  );
}

export async function simulateDeployStep(
  stepId: string,
  config: DeployConfig,
): Promise<SimulateStepResult> {
  return handle(
    await fetch(`${BASE_URL}/api/mcp-deploy/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step_id: stepId, config }),
    }),
  );
}

// ---- Feature 5: stream processing ----
export async function getStreamScenarios(): Promise<StreamScenarios> {
  return handle(await fetch(`${BASE_URL}/api/stream/scenarios`, { cache: 'no-store' }));
}

export async function simulateStream(
  scenarioId: string,
  count: number,
): Promise<StreamSimulation> {
  return handle(
    await fetch(`${BASE_URL}/api/stream/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId, count }),
    }),
  );
}

export { BASE_URL };
