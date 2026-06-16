import type { Metadata } from 'next';
import './globals.css';
import Nav from '@/components/Nav';
import Providers from './providers';

export const metadata: Metadata = {
  title: 'MongoDB on AWS — Demo',
  description:
    'Interactive demonstrations of MongoDB Atlas on AWS: search, vector search, agentic memory, MCP on Bedrock AgentCore, auto-embedding, and stream processing.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Nav />
          <main className="page-container">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
