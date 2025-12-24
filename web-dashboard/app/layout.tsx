import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'AIDN Dashboard - AI-Powered Insurance Distribution Network',
  description: 'Professional dashboard for AIDN voice agent and lead management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        {children}
      </body>
    </html>
  )
}