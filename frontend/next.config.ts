import type { NextConfig } from 'next'
import path from 'path'

const nextConfig: NextConfig = {
  // Required for Docker standalone output
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'http',  hostname: 'localhost' },
      { protocol: 'https', hostname: '*.onrender.com' },
    ],
  },
  // Proxy /api/** to the FastAPI backend running on port 8000 in the same container
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
  // Webpack alias so @/... imports resolve correctly in production builds
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(process.cwd(), '.'),
    }
    return config
  },
}

export default nextConfig


export default nextConfig
