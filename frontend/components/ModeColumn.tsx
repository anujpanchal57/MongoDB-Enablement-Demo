import { modeColor } from '@/lib/theme';
import type { SearchResponse } from '@/lib/types';
import QueryView from './QueryView';
import ResultCard from './ResultCard';

const TITLES: Record<string, string> = {
  fulltext: 'Full-Text',
  vector: 'Vector',
  hybrid: 'Hybrid (RRF)',
};

const SUBTITLES: Record<string, string> = {
  fulltext: 'Atlas Search · keyword relevance',
  vector: 'Voyage embeddings · semantic similarity',
  hybrid: 'Reciprocal Rank Fusion of both',
};

/** One column of the side-by-side comparison: a single search mode's results. */
export default function ModeColumn({ data }: { data?: SearchResponse }) {
  const mode = data?.mode ?? 'fulltext';
  const c = modeColor[mode];

  return (
    <div>
      <div
        style={{
          background: c.bg,
          color: c.fg,
          borderRadius: '10px 10px 0 0',
          padding: '12px 14px',
          borderBottom: `3px solid ${c.accent}`,
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 16 }}>{TITLES[mode]}</div>
        <div style={{ fontSize: 12, opacity: 0.85 }}>{SUBTITLES[mode]}</div>
        {data ? (
          <div style={{ fontSize: 11, marginTop: 4, opacity: 0.8 }}>
            {data.count} results · {data.took_ms} ms
          </div>
        ) : null}
        {data ? <QueryView data={data} accent={c.accent} /> : null}
      </div>
      <div style={{ paddingTop: 12 }}>
        {!data ? (
          <p className="muted" style={{ fontSize: 13 }}>
            No results yet.
          </p>
        ) : data.results.length === 0 ? (
          <p className="muted" style={{ fontSize: 13 }}>
            No matches.
          </p>
        ) : (
          data.results.map((hit, i) => (
            <ResultCard key={`${hit.id}-${i}`} hit={hit} rank={i + 1} accent={c.accent} />
          ))
        )}
      </div>
    </div>
  );
}
