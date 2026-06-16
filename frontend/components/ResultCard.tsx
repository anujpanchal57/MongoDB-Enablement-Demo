import type { MovieHit } from '@/lib/types';

interface Props {
  hit: MovieHit;
  rank: number;
  accent: string;
}

/** A single search result. Shows the within-mode rank prominently and, for
 *  hybrid results, the contributing full-text / vector ranks so the audience
 *  can see exactly how fusion combined the two signals. */
export default function ResultCard({ hit, rank, accent }: Props) {
  return (
    <div className="result-card">
      <div style={{ display: 'flex', gap: 10 }}>
        <span className="rank-badge" style={{ background: accent, color: '#fff' }}>
          {rank}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, lineHeight: 1.25 }}>
            {hit.title}
            {hit.year ? <span className="muted"> ({hit.year})</span> : null}
          </div>
          {hit.plot ? (
            <p
              className="muted"
              style={{
                margin: '4px 0 6px',
                fontSize: 13,
                lineHeight: 1.4,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {hit.plot}
            </p>
          ) : null}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
            {hit.genres?.slice(0, 3).map((g) => (
              <span
                key={g}
                style={{
                  fontSize: 11,
                  background: '#E8EDEB',
                  color: '#3D4F58',
                  borderRadius: 4,
                  padding: '2px 6px',
                }}
              >
                {g}
              </span>
            ))}
            {typeof hit.imdb_rating === 'number' ? (
              <span style={{ fontSize: 11, color: '#3D4F58' }}>★ {hit.imdb_rating.toFixed(1)}</span>
            ) : null}
          </div>
          {/* Ranking transparency line */}
          <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>
            {hit.fulltext_rank || hit.vector_rank ? (
              <>
                {hit.fulltext_rank ? `text #${hit.fulltext_rank}` : 'text —'}
                {'  ·  '}
                {hit.vector_rank ? `vector #${hit.vector_rank}` : 'vector —'}
                {typeof hit.fused_score === 'number'
                  ? `  ·  RRF ${hit.fused_score.toFixed(4)}`
                  : ''}
              </>
            ) : typeof hit.score === 'number' ? (
              `score ${hit.score.toFixed(4)}`
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
