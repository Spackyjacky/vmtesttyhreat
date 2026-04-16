/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ['twilio', 'resend'],
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.supabase.co',
        port: '',
        pathname: '/storage/v1/object/public/**',
      },
    ],
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Tell webpack to ignore Node.js-only modules on the client side
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        dns: false,
        child_process: false,
        'timers/promises': false,
      }
    }
    return config
  },
}

export default nextConfig
