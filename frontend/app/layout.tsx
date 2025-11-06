import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hack-A-Job',
  description: 'Automated job application tool',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

