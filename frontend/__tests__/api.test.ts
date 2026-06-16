/**
 * Unit tests for the API client. fetch is mocked so no backend is needed.
 */
import { compareSearch, getExamples, runSearch } from '@/lib/api';

const okJson = (body: unknown) =>
  Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response);

function mockFetch(impl: () => Promise<Response>) {
  const fn = jest.fn(impl);
  global.fetch = fn as unknown as typeof fetch;
  return fn;
}

describe('api client', () => {
  afterEach(() => jest.restoreAllMocks());

  it('runSearch posts query + mode and returns parsed response', async () => {
    const spy = mockFetch(() =>
      okJson({ mode: 'vector', query: 'x', count: 0, took_ms: 5, results: [], live: true }),
    );

    const res = await runSearch('a heist', 'vector', 5);

    expect(res.mode).toBe('vector');
    const init = spy.mock.calls[0][1];
    expect(init?.method).toBe('POST');
    expect(JSON.parse(init?.body as string)).toMatchObject({
      query: 'a heist',
      mode: 'vector',
      limit: 5,
    });
  });

  it('getExamples unwraps the examples array', async () => {
    mockFetch(() => okJson({ examples: [{ label: 'L', query: 'q', why: 'w' }] }));
    const examples = await getExamples();
    expect(examples).toHaveLength(1);
    expect(examples[0].label).toBe('L');
  });

  it('compareSearch builds a compare URL with the query', async () => {
    const spy = mockFetch(() => okJson({ query: 'q', modes: {}, atlas_reachable: true }));
    await compareSearch('space exploration', 8);
    const url = spy.mock.calls[0][0];
    expect(String(url)).toContain('/api/search/compare');
    expect(String(url)).toContain('q=space+exploration');
    expect(String(url)).toContain('limit=8');
  });

  it('throws with backend detail on error response', async () => {
    mockFetch(() =>
      Promise.resolve({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        json: () => Promise.resolve({ detail: 'MongoDB is not configured' }),
      } as Response),
    );
    await expect(runSearch('x', 'fulltext')).rejects.toThrow('MongoDB is not configured');
  });
});
