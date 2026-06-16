'use client';

import Button from '@leafygreen-ui/button';
import TextInput from '@leafygreen-ui/text-input';
import { useEffect, useState } from 'react';
import ModeColumn from '@/components/ModeColumn';
import { compareSearch, getExamples, getHealth } from '@/lib/api';
import type { CompareResponse, ExampleQuery } from '@/lib/types';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [examples, setExamples] = useState<ExampleQuery[]>([]);
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string | null>(null);

  useEffect(() => {
    getExamples()
      .then(setExamples)
      .catch(() => setExamples([]));
    getHealth()
      .then((h) => {
        if (!h.mongodb_reachable) setHealth('⚠ Atlas not reachable — check MONGODB_URI in .env');
        else if (!h.voyage_configured)
          setHealth('⚠ Voyage not configured — vector/hybrid will fail (set VOYAGE_API_KEY)');
        else setHealth(null);
      })
      .catch(() => setHealth('⚠ Backend not reachable — is FastAPI running on :8000?'));
  }, []);

  async function run(q: string) {
    const term = q.trim();
    if (!term) return;
    setQuery(term);
    setLoading(true);
    setError(null);
    try {
      setData(await compareSearch(term, topK));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Search failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, margin: '0 0 6px' }}>Search Comparison</h1>
      <p className="muted" style={{ marginTop: 0, maxWidth: 760 }}>
        One query, three strategies. Watch how <strong>full-text</strong> (keyword),{' '}
        <strong>vector</strong> (semantic), and <strong>hybrid</strong> (fused) ranking differ over
        the <code>embedded_movies</code> collection.
      </p>

      {health ? (
        <div
          style={{
            background: '#FEF7E0',
            border: '1px solid #FFC010',
            color: '#765000',
            borderRadius: 8,
            padding: '8px 12px',
            fontSize: 13,
            margin: '12px 0',
          }}
        >
          {health}
        </div>
      ) : null}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(query);
        }}
        style={{ display: 'flex', gap: 12, alignItems: 'flex-end', margin: '16px 0 4px' }}
      >
        <div style={{ flex: 1 }}>
          <TextInput
            label="Search query"
            aria-label="Search query"
            placeholder="e.g. a heist that goes wrong"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div style={{ width: 110 }}>
          <TextInput
            type="number"
            label="Top K"
            aria-label="Top K results"
            min={1}
            max={50}
            value={String(topK)}
            onChange={(e) => {
              const n = parseInt(e.target.value, 10);
              if (Number.isNaN(n)) setTopK(1);
              else setTopK(Math.min(50, Math.max(1, n)));
            }}
          />
        </div>
        <Button type="submit" variant="primary" disabled={loading}>
          {loading ? 'Searching…' : 'Compare modes'}
        </Button>
      </form>

      {examples.length > 0 ? (
        <>
          <div className="muted" style={{ fontSize: 12, marginTop: 12 }}>
            Try a curated example:
          </div>
          <div className="chip-row">
            {examples.map((ex) => (
              <button
                key={ex.label}
                type="button"
                className="chip"
                title={ex.why}
                onClick={() => run(ex.query)}
              >
                {ex.label}
              </button>
            ))}
          </div>
        </>
      ) : null}

      {error ? (
        <div
          style={{
            background: '#FDEDEE',
            border: '1px solid #DB3030',
            color: '#970606',
            borderRadius: 8,
            padding: '10px 12px',
            fontSize: 13,
            margin: '16px 0',
          }}
        >
          {error}
        </div>
      ) : null}

      {data ? (
        <div style={{ marginTop: 20 }}>
          <div className="muted" style={{ fontSize: 13, marginBottom: 10 }}>
            Results for <strong>“{data.query}”</strong>
          </div>
          <div className="compare-grid">
            <ModeColumn data={data.modes.fulltext} />
            <ModeColumn data={data.modes.vector} />
            <ModeColumn data={data.modes.hybrid} />
          </div>
        </div>
      ) : (
        !loading && (
          <p className="muted" style={{ marginTop: 24 }}>
            Enter a query or pick an example to see the three strategies side by side.
          </p>
        )
      )}
    </div>
  );
}
