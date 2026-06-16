'use client';

import Button from '@leafygreen-ui/button';
import TextInput from '@leafygreen-ui/text-input';
import { useEffect, useState } from 'react';
import {
  autoEmbedSearch,
  autoEmbedSetup,
  getAutoEmbedDataset,
  getAutoEmbedStatus,
} from '@/lib/api';
import { mongo } from '@/lib/theme';
import type {
  AutoEmbedDataset,
  AutoEmbedSearchResponse,
  AutoEmbedStatus,
} from '@/lib/types';

export default function AutoEmbedPage() {
  const [dataset, setDataset] = useState<AutoEmbedDataset | null>(null);
  const [status, setStatus] = useState<AutoEmbedStatus | null>(null);
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(8);
  const [results, setResults] = useState<AutoEmbedSearchResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAutoEmbedDataset().then(setDataset).catch(() => setDataset(null));
    refreshStatus();
  }, []);

  async function refreshStatus() {
    try {
      setStatus(await getAutoEmbedStatus());
    } catch {
      setStatus(null);
    }
  }

  async function onSetup() {
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const res = await autoEmbedSetup();
      setMsg(res.message);
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Setup failed');
    } finally {
      setBusy(false);
    }
  }

  async function onSearch(q: string) {
    const term = q.trim();
    if (!term) return;
    setQuery(term);
    setBusy(true);
    setError(null);
    try {
      setResults(await autoEmbedSearch(term, topK));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed');
      setResults(null);
    } finally {
      setBusy(false);
    }
  }

  const ready = status?.queryable;

  return (
    <div>
      <h1 style={{ fontSize: 30, margin: '0 0 6px' }}>Auto-Embedding Vector Index</h1>
      <p className="muted" style={{ marginTop: 0, maxWidth: 820 }}>
        Atlas can generate embeddings <strong>for you</strong>. You store plain text, declare a
        vector index with <code>type: &quot;autoEmbed&quot;</code> and a managed model, and query with a{' '}
        <strong>text string</strong> — no client-side embedding code at all. Contrast this with the{' '}
        <a href="/search">Search</a> demo, where we compute Voyage vectors ourselves.
      </p>

      {/* Index definition */}
      <div className="compare-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 16 }}>
        <div className="result-card">
          <div style={{ fontWeight: 700, marginBottom: 6 }}>The auto-embedding index</div>
          <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
            Model <strong>{dataset?.model}</strong> is managed by Atlas. No <code>plot_embedding</code>
            -style field is stored.
          </p>
          <pre
            style={{
              background: mongo.black,
              color: mongo.greenLight3,
              borderRadius: 6,
              padding: 12,
              fontSize: 12,
              overflowX: 'auto',
              margin: 0,
            }}
          >
            <code>{dataset ? JSON.stringify(dataset.index_definition, null, 2) : '...'}</code>
          </pre>
        </div>

        <div className="result-card">
          <div style={{ fontWeight: 700, marginBottom: 6 }}>1 · Set up the demo</div>
          <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
            Ingests {dataset?.count ?? '~20'} curated travel destinations (plain text) and creates
            the index. Atlas then embeds them automatically.
          </p>
          <Button variant="primary" onClick={onSetup} disabled={busy}>
            {busy ? 'Working…' : 'Ingest + create index'}
          </Button>
          <Button
            variant="default"
            onClick={refreshStatus}
            disabled={busy}
            style={{ marginLeft: 8 }}
          >
            Refresh status
          </Button>
          {status ? (
            <div style={{ marginTop: 12, fontSize: 13 }}>
              <div>
                Documents: <strong>{status.document_count}</strong>
              </div>
              <div>
                Index:{' '}
                <span
                  className="rank-badge"
                  style={{
                    background: ready ? mongo.greenLight2 : '#FEF3C7',
                    color: ready ? mongo.greenDark2 : '#92400E',
                    fontSize: 11,
                  }}
                >
                  {status.index_exists ? status.index_status || 'PENDING' : 'NOT CREATED'}
                </span>{' '}
                {ready ? '· queryable ✓' : '· building…'}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {msg ? (
        <div
          style={{
            background: mongo.greenLight3,
            border: `1px solid ${mongo.greenBase}`,
            color: mongo.greenDark3,
            borderRadius: 8,
            padding: '8px 12px',
            fontSize: 13,
            margin: '12px 0',
          }}
        >
          {msg}
        </div>
      ) : null}

      {/* Search */}
      <h2 style={{ fontSize: 20, marginTop: 28, marginBottom: 4 }}>2 · Search by meaning</h2>
      <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
        Type a natural-language idea. Atlas embeds your text and ranks destinations by semantic
        similarity — the words you type need not appear in any description.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSearch(query);
        }}
        style={{ display: 'flex', gap: 12, alignItems: 'flex-end', margin: '12px 0 4px' }}
      >
        <div style={{ flex: 1 }}>
          <TextInput
            label="Describe your ideal trip"
            aria-label="Search query"
            placeholder="e.g. a romantic secluded island honeymoon"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!ready}
          />
        </div>
        <div style={{ width: 110 }}>
          <TextInput
            type="number"
            label="Top K"
            aria-label="Top K"
            min={1}
            max={20}
            value={String(topK)}
            onChange={(e) => {
              const n = parseInt(e.target.value, 10);
              setTopK(Number.isNaN(n) ? 1 : Math.min(20, Math.max(1, n)));
            }}
          />
        </div>
        <Button type="submit" variant="primary" disabled={busy || !ready}>
          Search
        </Button>
      </form>

      {!ready ? (
        <p className="muted" style={{ fontSize: 12 }}>
          Search unlocks once the index status is <strong>READY</strong>.
        </p>
      ) : null}

      {dataset?.examples?.length ? (
        <div className="chip-row">
          {dataset.examples.map((ex) => (
            <button
              key={ex.label}
              type="button"
              className="chip"
              onClick={() => onSearch(ex.query)}
              disabled={!ready}
            >
              {ex.label}
            </button>
          ))}
        </div>
      ) : null}

      {error ? (
        <div
          style={{
            background: '#FDEDEE',
            border: `1px solid ${mongo.redBase}`,
            color: '#970606',
            borderRadius: 8,
            padding: '10px 12px',
            fontSize: 13,
            margin: '12px 0',
          }}
        >
          {error}
        </div>
      ) : null}

      {results ? (
        <div style={{ marginTop: 16 }}>
          <div className="muted" style={{ fontSize: 13, marginBottom: 8 }}>
            {results.count} results for <strong>“{results.query}”</strong> · {results.took_ms} ms
          </div>
          {results.results.map((d, i) => (
            <div key={d.id} className="result-card">
              <div style={{ display: 'flex', gap: 10 }}>
                <span
                  className="rank-badge"
                  style={{ background: mongo.blueBase, color: '#fff' }}
                >
                  {i + 1}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>
                    {d.name}
                    {d.country ? <span className="muted"> · {d.country}</span> : null}
                    {typeof d.score === 'number' ? (
                      <span className="muted" style={{ float: 'right', fontSize: 12 }}>
                        score {d.score.toFixed(4)}
                      </span>
                    ) : null}
                  </div>
                  <p className="muted" style={{ fontSize: 13, margin: '4px 0 6px' }}>
                    {d.description}
                  </p>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {d.tags.map((t) => (
                      <span
                        key={t}
                        style={{
                          fontSize: 11,
                          background: mongo.gray200,
                          color: mongo.gray700,
                          borderRadius: 4,
                          padding: '2px 6px',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                    {d.best_season ? (
                      <span style={{ fontSize: 11, color: mongo.gray700 }}>
                        · best: {d.best_season}
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
