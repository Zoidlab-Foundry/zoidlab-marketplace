import type { Metadata } from "next";
import "./globals.css";
import MarketplaceNav from "../components/MarketplaceNav";

export const metadata: Metadata = {
  title: "ZoidLab Marketplace",
  description: "Prototype, package, and deploy reusable AI agents across Nyquest.",
  icons: { icon: "/logo.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-bg text-ink">
        <MarketplaceNav />
        <main className="mx-auto w-full max-w-[1200px] px-5">{children}</main>
        <footer className="mx-auto mt-24 w-full max-w-[1200px] border-t border-line px-5 py-10 text-[12px] text-faint">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span>ZoidLab Marketplace · The agent app store for Nyquest.</span>
            <span className="flex gap-4">
              <a href="https://zoidlab.ai" className="hover:text-dim">zoidlab.ai</a>
              <a href="https://nyquest.ai" className="hover:text-dim">nyquest.ai</a>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
