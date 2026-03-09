import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.openalex.org',
        port: ''
      },
      {
        protocol: 'https',
        hostname: 'semanticscholar.org',
        port: ''
      },
      {
        protocol: 'https',
        hostname: 'www.semanticscholar.org',
        port: ''
      }
    ]
  },
  transpilePackages: ['geist']
};

export default nextConfig;
