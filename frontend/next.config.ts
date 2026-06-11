import type { NextConfig } from 'next'
import path from 'path'

const nextConfig: NextConfig = {
  // Required for Render — it injects a dynamic PORT at runtime
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'http',  hostname: 'localhost' },
      // Allow images from your Render backend URL
      { protocol: 'https', hostname: '*.onrender.com' },
    ],
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(process.cwd(), '.'),
    }
    return config;
  },
}

export default nextConfig
