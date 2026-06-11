import type { NextConfig } from 'next'

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
}

export default nextConfig
