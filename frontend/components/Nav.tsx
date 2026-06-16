import Link from 'next/link';

/** Top navigation bar linking to each feature. */
export default function Nav() {
  return (
    <nav className="nav">
      <Link href="/" className="brand">
        <span className="dot">●</span> MongoDB on AWS
      </Link>
      <span className="spacer" />
      <Link href="/search">Search</Link>
      <Link href="/memory">Agentic Memory</Link>
      <Link href="/mcp-deploy">MCP on AgentCore</Link>
      <Link href="/autoembed">Auto-Embedding</Link>
      {/* Stream Processing (Feature 5) temporarily hidden from the UI.
      <Link href="/stream">Stream Processing</Link>
      */}
    </nav>
  );
}
