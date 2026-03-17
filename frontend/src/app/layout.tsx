import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RentWatch - 賃貸価格モニター",
  description: "SUUMO・HOME'Sの賃貸価格を自動監視",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
