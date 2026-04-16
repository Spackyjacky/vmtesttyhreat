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
}

export default nextConfig
