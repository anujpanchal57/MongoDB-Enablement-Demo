/**
 * API-client tests for Features 2–5. fetch is mocked; no backend required.
 */
import {
  autoEmbedSearch,
  getDeploySteps,
  memoryChat,
  simulateDeployStep,
  simulateStream,
} from '@/lib/api';

const okJson = (body: unknown) =>
  Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response);

function mockFetch(impl: () => Promise<Response>) {
  const fn = jest.fn(impl);
  global.fetch = fn as unknown as typeof fetch;
  return fn;
}

describe('feature api clients', () => {
  afterEach(() => jest.restoreAllMocks());

  it('autoEmbedSearch posts query + limit', async () => {
    const spy = mockFetch(() => okJson({ query: 'x', count: 0, took_ms: 1, results: [] }));
    await autoEmbedSearch('island getaway', 5);
    const [url, init] = spy.mock.calls[0];
    expect(String(url)).toContain('/api/autoembed');
    expect(JSON.parse((init as RequestInit).body as string)).toMatchObject({
      query: 'island getaway',
      limit: 5,
    });
  });

  it('memoryChat sends thread_id + user_id', async () => {
    const spy = mockFetch(() =>
      okJson({ reply: 'hi', thread_id: 't', user_id: 'u', recalled: [], saved: [], live: true }),
    );
    const res = await memoryChat('hello', 'thread-A', 'demo-user');
    expect(res.reply).toBe('hi');
    const body = JSON.parse((spy.mock.calls[0][1] as RequestInit).body as string);
    expect(body).toMatchObject({ message: 'hello', thread_id: 'thread-A', user_id: 'demo-user' });
  });

  it('getDeploySteps GET without config', async () => {
    const spy = mockFetch(() =>
      okJson({ title: 't', source_repo: 'r', prerequisites: [], steps: [], config: {} }),
    );
    await getDeploySteps();
    expect(String(spy.mock.calls[0][0])).toContain('/api/mcp-deploy/steps');
    // No method => GET
    expect((spy.mock.calls[0][1] as RequestInit | undefined)?.method).toBeUndefined();
  });

  it('simulateDeployStep posts step_id + config', async () => {
    const spy = mockFetch(() =>
      okJson({ step_id: 'build', ok: true, simulated: true, output: 'done', duration_ms: 10 }),
    );
    const res = await simulateDeployStep('build', {
      account_id: '1',
      region: 'us-east-1',
      repo_name: 'r',
      runtime_name: 'rt',
      connection_string: 'mongodb://x',
    });
    expect(res.ok).toBe(true);
    expect(JSON.parse((spy.mock.calls[0][1] as RequestInit).body as string).step_id).toBe('build');
  });

  it('simulateStream posts scenario_id + count', async () => {
    const spy = mockFetch(() =>
      okJson({ scenario_id: 'kinesis_to_atlas', direction: 'kinesis_to_atlas', processed: 3, to_sink: 2, to_dlq: 1, records: [] }),
    );
    const res = await simulateStream('kinesis_to_atlas', 3);
    expect(res.processed).toBe(3);
    expect(JSON.parse((spy.mock.calls[0][1] as RequestInit).body as string)).toMatchObject({
      scenario_id: 'kinesis_to_atlas',
      count: 3,
    });
  });
});
