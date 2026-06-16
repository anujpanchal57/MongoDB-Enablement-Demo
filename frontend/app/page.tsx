import Link from 'next/link';

const FEATURES = [
  {
    n: 1,
    title: 'Search: Full-Text, Vector & Hybrid',
    desc: 'Compare keyword, semantic, and fused ranking over the embedded_movies collection — side by side.',
    href: '/search',
    live: true,
  },
  {
    n: 2,
    title: 'Agentic Memory (LangChain + LangGraph)',
    desc: 'Persist and recall long-term conversational memory in MongoDB across threads.',
    href: '/memory',
    live: true,
  },
  {
    n: 3,
    title: 'Deploy MCP Server on Bedrock AgentCore',
    desc: 'Guided, interactive walkthrough of deploying the MongoDB MCP server to AgentCore Runtime.',
    href: '/mcp-deploy',
    live: true,
  },
  {
    n: 4,
    title: 'Auto-Embedding Vector Index',
    desc: 'Create a vector index with Atlas automated embedding and query it instantly.',
    href: '/autoembed',
    live: true,
  },
  // Stream Processing (Feature 5) temporarily hidden from the UI.
  // {
  //   n: 5,
  //   title: 'Stream Processing ↔ AWS Kinesis',
  //   desc: 'Stream data between MongoDB Atlas and Kinesis Data Streams through a stream processor.',
  //   href: '/stream',
  //   live: true,
  // },
];

export default function Home() {
  return (
    <div>
      <section className="hero">
        <h1 style={{ fontSize: 40, margin: '0 0 12px', fontWeight: 700 }}>
          MongoDB <span className="leaf">on AWS</span>
        </h1>
        <p style={{ fontSize: 18, maxWidth: 720, opacity: 0.9, lineHeight: 1.5 }}>
          An interactive demonstration suite for showcasing MongoDB Atlas capabilities running on
          AWS — search, semantic retrieval, agentic memory, MCP on Bedrock AgentCore, automated
          embeddings, and stream processing.
        </p>
      </section>

      <div className="feature-grid">
        {FEATURES.map((f) => (
          <Link
            key={f.n}
            href={f.href}
            className="result-card"
            style={{ display: 'block', textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="muted" style={{ fontSize: 13 }}>
                Feature {f.n}
              </span>
              <span
                className="rank-badge"
                style={{
                  background: f.live ? '#C0FAE6' : '#E8EDEB',
                  color: f.live ? '#00684A' : '#3D4F58',
                }}
              >
                {f.live ? 'LIVE' : 'SOON'}
              </span>
            </div>
            <h3 style={{ margin: '8px 0 6px', fontSize: 18 }}>{f.title}</h3>
            <p className="muted" style={{ margin: 0, fontSize: 14, lineHeight: 1.45 }}>
              {f.desc}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
