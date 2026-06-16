'use client';

import Button from '@leafygreen-ui/button';
import TextInput from '@leafygreen-ui/text-input';
import { useEffect, useState } from 'react';
import { getDeploySteps, simulateDeployStep } from '@/lib/api';
import { mongo } from '@/lib/theme';
import type { DeployConfig, DeploySteps, SimulateStepResult } from '@/lib/types';

const FIELDS: { key: keyof DeployConfig; label: string }[] = [
  { key: 'account_id', label: 'AWS Account ID' },
  { key: 'region', label: 'Region' },
  { key: 'repo_name', label: 'ECR repo name' },
  { key: 'runtime_name', label: 'AgentCore runtime name' },
  { key: 'connection_string', label: 'MongoDB connection string (mongodb://)' },
];

function CodeBlock({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => {
          navigator.clipboard?.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        }}
        style={{
          position: 'absolute',
          top: 6,
          right: 6,
          fontSize: 11,
          background: mongo.greenDark2,
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          padding: '2px 8px',
          cursor: 'pointer',
        }}
      >
        {copied ? 'Copied' : 'Copy'}
      </button>
      <pre
        style={{
          background: mongo.black,
          color: mongo.greenLight3,
          borderRadius: 6,
          padding: '12px 14px',
          fontSize: 12,
          lineHeight: 1.5,
          overflowX: 'auto',
          margin: '6px 0',
        }}
      >
        <code>{text}</code>
      </pre>
    </div>
  );
}

export default function McpDeployPage() {
  const [config, setConfig] = useState<DeployConfig>({
    account_id: '123456789012',
    region: 'us-east-1',
    repo_name: 'mongodb-mcp-server',
    runtime_name: 'mongodb_mcp',
    connection_string: 'mongodb://<user>:<pass>@<host>:27017/?directConnection=true',
  });
  const [data, setData] = useState<DeploySteps | null>(null);
  const [results, setResults] = useState<Record<string, SimulateStepResult>>({});
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    getDeploySteps().then((d) => {
      setData(d);
      setConfig(d.config);
    });
  }, []);

  async function applyConfig() {
    const d = await getDeploySteps(config);
    setData(d);
    setResults({});
  }

  async function runStep(stepId: string) {
    setRunning(stepId);
    try {
      const res = await simulateDeployStep(stepId, config);
      setResults((prev) => ({ ...prev, [stepId]: res }));
    } finally {
      setRunning(null);
    }
  }

  const completed = Object.values(results).filter((r) => r.ok).length;

  return (
    <div>
      <h1 style={{ fontSize: 30, margin: '0 0 6px' }}>Deploy MCP Server on Bedrock AgentCore</h1>
      <p className="muted" style={{ marginTop: 0, maxWidth: 880 }}>
        A guided walkthrough that turns the{' '}
        <a href={data?.source_repo} target="_blank" rel="noreferrer">
          mongodb-mcp-server/deploy/aws
        </a>{' '}
        instructions into copy-paste-ready commands for <strong>your</strong> account. Each step can
        be <strong>simulated</strong> — no real AWS calls, safe to run live.
      </p>

      {/* Config */}
      <div className="result-card" style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Your deployment parameters</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
          {FIELDS.map((f) => (
            <TextInput
              key={f.key}
              label={f.label}
              aria-label={f.label}
              value={config[f.key]}
              onChange={(e) => setConfig((c) => ({ ...c, [f.key]: e.target.value }))}
            />
          ))}
        </div>
        <Button variant="primary" onClick={applyConfig} style={{ marginTop: 12 }}>
          Apply to commands
        </Button>
      </div>

      {/* Prerequisites */}
      {data ? (
        <div className="result-card" style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Prerequisites</div>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {data.prerequisites.map((p, i) => (
              <li key={i} className="muted" style={{ fontSize: 13, marginBottom: 4 }}>
                {p}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Progress */}
      {data ? (
        <div className="muted" style={{ fontSize: 13, marginBottom: 10 }}>
          Progress: <strong>{completed}</strong> / {data.steps.length} steps simulated
        </div>
      ) : null}

      {/* Steps */}
      {data?.steps.map((step, idx) => {
        const res = results[step.id];
        return (
          <div key={step.id} className="result-card" style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span
                className="rank-badge"
                style={{
                  background: res?.ok ? mongo.greenBase : mongo.gray200,
                  color: res?.ok ? '#fff' : mongo.gray700,
                }}
              >
                {res?.ok ? '✓' : idx + 1}
              </span>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{step.title}</div>
            </div>
            <p className="muted" style={{ fontSize: 13, margin: '6px 0' }}>
              {step.summary}
            </p>
            {step.commands.map((cmd, i) => (
              <CodeBlock key={i} text={cmd} />
            ))}
            {Object.keys(step.env).length > 0 ? (
              <div style={{ marginTop: 6 }}>
                <div className="muted" style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                  Environment variables
                </div>
                {Object.entries(step.env).map(([k, v]) => (
                  <div key={k} style={{ fontFamily: 'monospace', fontSize: 12 }}>
                    <span style={{ color: mongo.purpleBase }}>{k}</span>=
                    <span className="muted">{v}</span>
                  </div>
                ))}
              </div>
            ) : null}
            {step.notes.map((n, i) => (
              <div key={i} style={{ fontSize: 12, color: mongo.greenDark2, marginTop: 4 }}>
                ⓘ {n}
              </div>
            ))}
            <div style={{ marginTop: 10 }}>
              <Button
                variant={res?.ok ? 'default' : 'primary'}
                onClick={() => runStep(step.id)}
                disabled={running === step.id}
              >
                {running === step.id ? 'Running…' : res?.ok ? 'Re-run (simulated)' : 'Simulate this step'}
              </Button>
            </div>
            {res ? (
              <div style={{ marginTop: 10 }}>
                <div className="muted" style={{ fontSize: 11, marginBottom: 2 }}>
                  Simulated output · {res.duration_ms} ms
                </div>
                <pre
                  style={{
                    background: '#02231b',
                    color: mongo.greenLight2,
                    borderRadius: 6,
                    padding: '10px 12px',
                    fontSize: 12,
                    overflowX: 'auto',
                    margin: 0,
                  }}
                >
                  <code>{res.output}</code>
                </pre>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
