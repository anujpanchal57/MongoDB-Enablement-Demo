'use client';

import Button from '@leafygreen-ui/button';
import TextInput from '@leafygreen-ui/text-input';
import { useEffect, useRef, useState } from 'react';
import {
  clearMemories,
  getMemories,
  getMemoryDemoScript,
  memoryChat,
} from '@/lib/api';
import { mongo } from '@/lib/theme';
import type { MemoryDemoScript, MemoryItem, RecalledMemory } from '@/lib/types';

interface Turn {
  role: 'user' | 'assistant';
  content: string;
  recalled?: RecalledMemory[];
  saved?: string[];
}

const USER_ID = 'demo-user';

export default function MemoryPage() {
  const [threadId, setThreadId] = useState('thread-A');
  const [transcripts, setTranscripts] = useState<Record<string, Turn[]>>({});
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [script, setScript] = useState<MemoryDemoScript | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const turns = transcripts[threadId] ?? [];

  useEffect(() => {
    getMemoryDemoScript().then(setScript).catch(() => setScript(null));
    refreshMemories();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length]);

  async function refreshMemories() {
    try {
      const list = await getMemories(USER_ID);
      setMemories(list.memories);
    } catch {
      setMemories([]);
    }
  }

  function appendTurn(thread: string, turn: Turn) {
    setTranscripts((prev) => ({ ...prev, [thread]: [...(prev[thread] ?? []), turn] }));
  }

  async function send(message: string, thread: string) {
    const text = message.trim();
    if (!text) return;
    setError(null);
    setBusy(true);
    appendTurn(thread, { role: 'user', content: text });
    try {
      const res = await memoryChat(text, thread, USER_ID);
      appendTurn(thread, {
        role: 'assistant',
        content: res.reply,
        recalled: res.recalled,
        saved: res.saved,
      });
      await refreshMemories();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chat failed');
    } finally {
      setBusy(false);
    }
  }

  async function runStep(thread: string, message: string) {
    setThreadId(thread);
    await send(message, thread);
  }

  async function onClear() {
    setBusy(true);
    try {
      await clearMemories(USER_ID);
      await refreshMemories();
      setTranscripts({});
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 30, margin: '0 0 6px' }}>Agentic Memory</h1>
      <p className="muted" style={{ marginTop: 0, maxWidth: 860 }}>
        A <strong>LangGraph</strong> agent (Claude on Bedrock) with memory in MongoDB. Each thread&apos;s
        conversation is checkpointed (<em>short-term</em> memory); durable facts about you are stored
        and <strong>recalled across threads</strong> via Voyage embeddings (<em>long-term</em> memory).
      </p>

      {/* Demo script */}
      {script ? (
        <div className="result-card" style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Guided demo — prove cross-thread recall</div>
          <ol style={{ margin: '0 0 10px', paddingLeft: 18 }}>
            {script.steps.map((s, i) => (
              <li key={i} style={{ fontSize: 13, marginBottom: 8 }}>
                <span
                  style={{
                    fontFamily: 'monospace',
                    fontSize: 11,
                    background: mongo.gray200,
                    padding: '1px 5px',
                    borderRadius: 4,
                    marginRight: 6,
                  }}
                >
                  {s.thread}
                </span>
                <button
                  type="button"
                  className="chip"
                  disabled={busy}
                  onClick={() => runStep(s.thread, s.message)}
                >
                  ▶ {s.message}
                </button>
                <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                  {s.note}
                </div>
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      <div className="compare-grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        {/* Chat column */}
        <div>
          {/* Thread switcher */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
            <span className="muted" style={{ fontSize: 13 }}>
              Thread:
            </span>
            {['thread-A', 'thread-B'].map((t) => (
              <button
                key={t}
                type="button"
                className="chip"
                onClick={() => setThreadId(t)}
                style={
                  threadId === t
                    ? { borderColor: mongo.greenBase, background: mongo.greenLight3, fontWeight: 600 }
                    : undefined
                }
              >
                {t}
              </button>
            ))}
            <span className="muted" style={{ fontSize: 12 }}>
              (switching threads keeps long-term memory, resets the conversation)
            </span>
          </div>

          <div
            style={{
              border: `1px solid ${mongo.gray200}`,
              borderRadius: 10,
              padding: 14,
              minHeight: 280,
              background: mongo.white,
            }}
          >
            {turns.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>
                No messages in <strong>{threadId}</strong> yet. Say something about yourself, then
                switch threads and watch the agent recall it.
              </p>
            ) : (
              turns.map((t, i) => (
                <div key={i} style={{ marginBottom: 14 }}>
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: t.role === 'user' ? mongo.gray700 : mongo.greenDark2,
                      marginBottom: 2,
                    }}
                  >
                    {t.role === 'user' ? 'You' : 'Agent'}
                  </div>
                  <div style={{ fontSize: 14, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                    {t.content}
                  </div>
                  {t.recalled && t.recalled.length > 0 ? (
                    <div style={{ marginTop: 6 }}>
                      <span className="muted" style={{ fontSize: 11 }}>
                        🧠 recalled:
                      </span>{' '}
                      {t.recalled.map((m, j) => (
                        <span
                          key={j}
                          title={`similarity ${m.score}`}
                          style={{
                            fontSize: 11,
                            background: '#EAF1FF',
                            color: '#0C2A66',
                            borderRadius: 4,
                            padding: '2px 6px',
                            marginRight: 4,
                          }}
                        >
                          {m.text} ({m.score})
                        </span>
                      ))}
                    </div>
                  ) : null}
                  {t.saved && t.saved.length > 0 ? (
                    <div style={{ marginTop: 4 }}>
                      <span className="muted" style={{ fontSize: 11 }}>
                        💾 saved:
                      </span>{' '}
                      {t.saved.map((s, j) => (
                        <span
                          key={j}
                          style={{
                            fontSize: 11,
                            background: mongo.greenLight2,
                            color: mongo.greenDark3,
                            borderRadius: 4,
                            padding: '2px 6px',
                            marginRight: 4,
                          }}
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))
            )}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input, threadId);
              setInput('');
            }}
            style={{ display: 'flex', gap: 8, alignItems: 'flex-end', marginTop: 10 }}
          >
            <div style={{ flex: 1 }}>
              <span id="chat-input-label" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>
                Message the agent
              </span>
              <TextInput
                aria-labelledby="chat-input-label"
                placeholder={`Message the agent on ${threadId}…`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={busy}
              />
            </div>
            <Button type="submit" variant="primary" disabled={busy}>
              {busy ? 'Thinking…' : 'Send'}
            </Button>
          </form>
          {error ? (
            <div
              style={{
                background: '#FDEDEE',
                border: `1px solid ${mongo.redBase}`,
                color: '#970606',
                borderRadius: 8,
                padding: '8px 12px',
                fontSize: 13,
                marginTop: 10,
              }}
            >
              {error}
            </div>
          ) : null}
        </div>

        {/* Long-term memory panel */}
        <div>
          <div
            style={{
              background: mongo.black,
              color: mongo.white,
              borderRadius: '10px 10px 0 0',
              padding: '10px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontWeight: 700, fontSize: 14 }}>
              Long-term memory ({memories.length})
            </span>
            <button
              type="button"
              onClick={onClear}
              disabled={busy || memories.length === 0}
              style={{
                background: 'transparent',
                color: mongo.greenBase,
                border: `1px solid ${mongo.greenDark1}`,
                borderRadius: 6,
                fontSize: 11,
                padding: '3px 8px',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          </div>
          <div
            style={{
              border: `1px solid ${mongo.gray200}`,
              borderTop: 'none',
              borderRadius: '0 0 10px 10px',
              padding: 12,
              minHeight: 260,
            }}
          >
            <div className="muted" style={{ fontSize: 11, marginBottom: 8 }}>
              Stored in <code>{`${'agentic_memory'}.long_term_memories`}</code>, recalled by any thread.
            </div>
            {memories.length === 0 ? (
              <p className="muted" style={{ fontSize: 13 }}>
                No memories yet.
              </p>
            ) : (
              memories.map((m) => (
                <div
                  key={m.id}
                  style={{
                    fontSize: 13,
                    padding: '6px 8px',
                    background: mongo.gray100,
                    borderRadius: 6,
                    marginBottom: 6,
                  }}
                >
                  {m.text}
                  {m.thread_id ? (
                    <span className="muted" style={{ fontSize: 11 }}>
                      {' '}
                      · from {m.thread_id}
                    </span>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
