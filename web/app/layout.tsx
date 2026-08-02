import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ad Performance – Board of Innovation",
  description: "Ad, platform, and weekly coverage overview for the BOI ad set.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
