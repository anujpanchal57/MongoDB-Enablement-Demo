'use client';

import Button from '@leafygreen-ui/button';
import TextInput from '@leafygreen-ui/text-input';
import { useEffect, useState } from 'react';
import { getStreamScenarios, simulateStream } from '@/lib/api';
import { mongo } from '@/lib/theme';
import type { StreamScenario, StreamScenarios, StreamSimulation } from '@/lib/types';

const SINK_STYLE: Record<string, { bg: string; fg: string; label: string }> = {
  'merge:atlas': { bg: mongo.greenLight2, fg: mongo.greenDark3, label: '→ Atlas ($merge)' },
  'emit:kinesis': { bg: '#EAF1FF', fg: '#0C2A66', label: '→ Kinesis ($emit)' },
  dlq: { bg: '#FDEDEE', fg: '#970606', label: 'dead-letter queue' },
};

function Json({ value }: { value: unknown }) {
  return (
    <pre
      style={{
        background: mongo.black,
        color: mongo.greenLight3,
        borderRadius: 6,
        padding: '10px 12px',
        fontSize: 11.5,
        lineHeight: 1.45,
        overflowX: 'auto',
        margin: 0,
      }}
    >
      <code>{JSON.stringify(value, null, 2)}</code>
    </pre>
  );
}

export default function StreamPage() {
  const [data, setData] = useState<StreamScenarios | null>(null);
  const [scenarioId, setScenarioId] = useState('kinesis_to_atlas');
  const [count, setCount] = useState(8);
  const [sim, setSim] = useState<StreamSimulation | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getStreamScenarios().then(setData);
  }, []);

  const scenario: StreamScenario | undefined = data?.scenarios.find((s) => s.id === scenarioId);

  async function run() {
    setBusy(true);
    try {
      setSim(await simulateStream(scenarioId, count));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, margin: '0 0 6px' }}>Stream Processing ↔ AWS Kinesis</h1>
      <p className="muted" style={{ marginTop: 0, maxWidth: 880 }}>
        Atlas Stream Processing connects MongoDB and{' '}
        <strong>AWS Kinesis Data Streams</strong>. Pick a direction to see the real connection
        registry, the stream-processor pipeline, and the management commands — then push synthetic
        IoT telemetry through it and watch each record land in a sink or the dead-letter queue.
      </p>

      {/* Scenario tabs */}
      <div style={{ display: 'flex', gap: 8, margin: '14px 0' }}>
        {data?.scenarios.map((s) => (
          <button
            key={s.id}
            type="button"
            className="chip"
            onClick={() => {
              setScenarioId(s.id);
              setSim(null);
            }}
            style={
              scenarioId === s.id
                ? { borderColor: mongo.greenBase, background: mongo.greenLight3, fontWeight: 600 }
                : undefined
            }
          >
            {s.title}
          </button>
        ))}
      </div>

      {scenario ? (
        <>
          <p className="muted" style={{ fontSize: 14 }}>
            {scenario.summary}
          </p>

          <div className="compare-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 8 }}>
            <div className="result-card">
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Connection registry</div>
              <Json value={scenario.connections} />
            </div>
            <div className="result-card">
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Stream processor pipeline</div>
              <Json value={scenario.pipeline} />
            </div>
          </div>

          <div className="result-card" style={{ marginTop: 12 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Manage the processor (mongosh)</div>
            <Json value={scenario.management} />
          </div>

          {/* Simulate */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', margin: '18px 0 6px' }}>
            <div style={{ width: 140 }}>
              <TextInput
                type="number"
                label="Events to stream"
                aria-label="Events to stream"
                min={1}
                max={30}
                value={String(count)}
                onChange={(e) => {
                  const n = parseInt(e.target.value, 10);
                  setCount(Number.isNaN(n) ? 1 : Math.min(30, Math.max(1, n)));
                }}
              />
            </div>
            <Button variant="primary" onClick={run} disabled={busy}>
              {busy ? 'Streaming…' : '▶ Stream events'}
            </Button>
          </div>

          {sim ? (
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', gap: 16, marginBottom: 10, fontSize: 13 }}>
                <span>
                  Processed: <strong>{sim.processed}</strong>
                </span>
                <span style={{ color: mongo.greenDark2 }}>
                  To sink: <strong>{sim.to_sink}</strong>
                </span>
                <span style={{ color: mongo.redBase }}>
                  To DLQ: <strong>{sim.to_dlq}</strong>
                </span>
              </div>
              {sim.records.map((r) => {
                const style = SINK_STYLE[r.sink] ?? SINK_STYLE.dlq;
                return (
                  <div
                    key={r.seq}
                    className="result-card"
                    style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: 12, alignItems: 'center' }}
                  >
                    <div style={{ fontFamily: 'monospace', fontSize: 11.5 }}>
                      {JSON.stringify(r.source)}
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <span
                        className="rank-badge"
                        style={{ background: style.bg, color: style.fg, fontSize: 11, whiteSpace: 'nowrap' }}
                      >
                        {style.label}
                      </span>
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: 11.5, color: mongo.gray700 }}>
                      {r.output ? JSON.stringify(r.output) : <em>dropped</em>}
                      {r.note ? (
                        <div style={{ fontSize: 10.5, color: style.fg }}>{r.note}</div>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
