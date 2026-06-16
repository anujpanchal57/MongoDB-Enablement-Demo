import type { SearchResponse } from '@/lib/types';

/** Collapsible view of the actual MongoDB query/pipeline executed for a mode.
 *  This is what makes the demo concrete: the audience sees the real
 *  $search / $vectorSearch / RRF that produced the results. */
export default function QueryView({ data, accent }: { data: SearchResponse; accent: string }) {
  const q = data.query_used;
  if (!q) return null;

  // Render order: full-text pipeline, vector pipeline, then the fusion note.
  const fusion = typeof q.fusion === 'string' ? (q.fusion as string) : null;
  const pipelines: [string, unknown][] = Object.entries(q).filter(([k]) => k !== 'fusion');

  return (
    <details style={{ marginTop: 8 }}>
      <summary
        style={{
          cursor: 'pointer',
          fontSize: 12,
          fontWeight: 600,
          color: accent,
          userSelect: 'none',
        }}
      >
        Show query
      </summary>
      <div style={{ marginTop: 8 }}>
        {pipelines.map(([label, pipeline]) => (
          <div key={label} style={{ marginBottom: 8 }}>
            {pipelines.length > 1 ? (
              <div className="muted" style={{ fontSize: 11, marginBottom: 2, fontWeight: 600 }}>
                {label} pipeline
              </div>
            ) : null}
            <pre
              style={{
                background: '#001E2B',
                color: '#E3FCF7',
                borderRadius: 6,
                padding: '10px 12px',
                fontSize: 11,
                lineHeight: 1.45,
                overflowX: 'auto',
                margin: 0,
              }}
            >
              <code>{JSON.stringify(pipeline, null, 2)}</code>
            </pre>
          </div>
        ))}
        {fusion ? (
          <div className="muted" style={{ fontSize: 11, fontStyle: 'italic' }}>
            {fusion}
          </div>
        ) : null}
      </div>
    </details>
  );
}
