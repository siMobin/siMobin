import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "siMobin",
  description:
    "Md. Shakibul Islam Mobin - A passionate Full Stack Developer from BD",
  keywords: [
    "siMobin",
    "Full Stack Developer",
    "Bangladesh",
    "Portfolio",
    "Web Developer",
    "Shakibul Islam Mobin",
  ],
  authors: [
    { name: "Md. Shakibul Islam Mobin", url: "https://simobin.vercel.app" },
  ],
  creator: "siMobin",
  publisher: "siMobin",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
        <Analytics />
      </body>
    </html>
  );
}
