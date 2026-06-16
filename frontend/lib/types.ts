// Shared types mirroring the FastAPI response models (app/models/search.py).

export type SearchMode = 'fulltext' | 'vector' | 'hybrid';

export interface MovieHit {
  id: string;
  title: string;
  year?: number | null;
  plot?: string | null;
  genres: string[];
  cast: string[];
  poster?: string | null;
  imdb_rating?: number | null;
  score?: number | null;
  fulltext_rank?: number | null;
  vector_rank?: number | null;
  fused_score?: number | null;
}

export interface SearchResponse {
  mode: SearchMode;
  query: string;
  count: number;
  took_ms: number;
  results: MovieHit[];
  live: boolean;
  note?: string | null;
  // The actual pipeline(s) executed. Keys vary by mode:
  //  fulltext -> { fulltext: [...] }
  //  vector   -> { vector: [...] }   (queryVector elided to a preview string)
  //  hybrid   -> { fulltext: [...], vector: [...], fusion: "..." }
  query_used?: Record<string, unknown> | null;
}

export interface CompareResponse {
  query: string;
  modes: Record<SearchMode, SearchResponse>;
  atlas_reachable: boolean;
}

export interface ExampleQuery {
  label: string;
  query: string;
  why: string;
}

// ---- Feature 4: auto-embedding ----
export interface DestinationHit {
  id: string;
  name: string;
  country?: string | null;
  region?: string | null;
  description?: string | null;
  tags: string[];
  best_season?: string | null;
  score?: number | null;
}

export interface AutoEmbedSearchResponse {
  query: string;
  count: number;
  took_ms: number;
  results: DestinationHit[];
  query_used?: Record<string, unknown> | null;
}

export interface AutoEmbedDataset {
  count: number;
  sample: Array<Record<string, unknown>>;
  index_definition: Record<string, unknown>;
  model: string;
  examples: { label: string; query: string }[];
}

export interface AutoEmbedStatus {
  collection: string;
  document_count: number;
  index_name: string;
  index_exists: boolean;
  index_status?: string | null;
  queryable: boolean;
}

export interface AutoEmbedSetup {
  collection: string;
  index: string;
  model: string;
  inserted: number;
  index_created: boolean;
  index_definition: Record<string, unknown>;
  message: string;
}

// ---- Feature 2: agentic memory ----
export interface RecalledMemory {
  text: string;
  score: number;
  thread_id?: string | null;
}

export interface ChatResponse {
  reply: string;
  thread_id: string;
  user_id: string;
  recalled: RecalledMemory[];
  saved: string[];
  live: boolean;
  note?: string | null;
}

export interface MemoryItem {
  id: string;
  user_id: string;
  text: string;
  thread_id?: string | null;
  created_at?: string | null;
}

export interface MemoryList {
  user_id: string;
  count: number;
  memories: MemoryItem[];
}

export interface MemoryDemoStep {
  thread: string;
  message: string;
  note: string;
}

export interface MemoryDemoScript {
  user_id: string;
  steps: MemoryDemoStep[];
}

// ---- Feature 3: MCP on AgentCore ----
export interface DeployStep {
  id: string;
  title: string;
  summary: string;
  commands: string[];
  env: Record<string, string>;
  notes: string[];
  docs?: string | null;
}

export interface DeployConfig {
  account_id: string;
  region: string;
  repo_name: string;
  runtime_name: string;
  connection_string: string;
}

export interface DeploySteps {
  title: string;
  source_repo: string;
  prerequisites: string[];
  steps: DeployStep[];
  config: DeployConfig;
}

export interface SimulateStepResult {
  step_id: string;
  ok: boolean;
  simulated: boolean;
  output: string;
  duration_ms: number;
}

// ---- Feature 5: stream processing ----
export interface StreamScenario {
  id: string;
  title: string;
  direction: string;
  summary: string;
  connections: Array<Record<string, unknown>>;
  pipeline: Array<Record<string, unknown>>;
  management: string[];
}

export interface StreamScenarios {
  title: string;
  docs: string[];
  scenarios: StreamScenario[];
}

export interface StreamRecord {
  seq: number;
  source: Record<string, unknown>;
  output?: Record<string, unknown> | null;
  sink: string;
  note?: string | null;
}

export interface StreamSimulation {
  scenario_id: string;
  direction: string;
  processed: number;
  to_sink: number;
  to_dlq: number;
  records: StreamRecord[];
}
