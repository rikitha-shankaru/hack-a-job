import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Hack-A-Job - AI-Powered Job Application Assistant',
  description: 'AI-powered job search and application assistant that tailors your resume and cover letter for each job',
  keywords: ['job search', 'resume tailoring', 'AI', 'job application', 'career'],
  authors: [{ name: 'Hack-A-Job' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#7c3aed',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  )
}
