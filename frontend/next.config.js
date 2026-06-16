/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // LeafyGreen UI ships untranspiled ESM/emotion; Next must transpile it.
  transpilePackages: [
    '@leafygreen-ui/leafygreen-provider',
    '@leafygreen-ui/lib',
    '@leafygreen-ui/tokens',
    '@leafygreen-ui/palette',
    '@leafygreen-ui/typography',
    '@leafygreen-ui/button',
    '@leafygreen-ui/card',
    '@leafygreen-ui/text-input',
    '@leafygreen-ui/segmented-control',
    '@leafygreen-ui/badge',
    '@leafygreen-ui/banner',
    '@leafygreen-ui/icon',
    '@leafygreen-ui/loading-indicator',
  ],
  // Allow remote movie posters (embedded_movies stores external poster URLs).
  images: {
    remotePatterns: [{ protocol: 'https', hostname: '**' }],
  },
};

module.exports = nextConfig;
