"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser } from "../lib/useUser";

const LINKS = [
  { href: "/", label: "Marketplace" },
  { href: "/agents", label: "Agents" },
  { href: "/my-agents", label: "My Agents", auth: true },
  { href: "/submit", label: "Submit", auth: true },
];

export default function MarketplaceNav() {
  const pathname = usePathname();
  const { user, authed } = useUser();
  const is = (h: string) => (h === "/" ? pathname === "/" : pathname.startsWith(h));

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1200px] items-center gap-6 px-5">
        <Link href="/" className="flex items-center gap-2.5">
          <img src="/logo.svg" alt="" className="h-6 w-6" />
          <span className="text-[14px] font-semibold tracking-tight">
            ZoidLab <span className="text-dim font-normal">Marketplace</span>
          </span>
        </Link>
        <nav className="hidden items-center gap-1 sm:flex">
          {LINKS.filter((l) => !l.auth || authed).map((l) => (
            <Link key={l.href} href={l.href}
              className={`rounded-md px-3 py-1.5 text-[13px] transition ${is(l.href) ? "bg-white/10 text-ink" : "text-dim hover:text-ink hover:bg-white/5"}`}>
              {l.label}
            </Link>
          ))}
          {user?.admin && (
            <Link href="/admin/review"
              className={`rounded-md px-3 py-1.5 text-[13px] ${is("/admin") ? "bg-white/10 text-ink" : "text-vi hover:bg-white/5"}`}>
              Admin
            </Link>
          )}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <Link href="/agents" className="hidden rounded-lg border border-line px-3 py-1.5 text-[12px] text-dim hover:text-ink md:block">Browse</Link>
          {authed ? (
            <span className="flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-[12px]">
              <span className="h-1.5 w-1.5 rounded-full bg-ok" />
              {user?.name?.split(" ")[0] || user?.email?.split("@")[0] || "Signed in"}
            </span>
          ) : (
            <a href="https://app.nyquest.ai" className="rounded-lg bg-vi px-3.5 py-1.5 text-[12px] font-semibold text-white hover:opacity-90">Sign in</a>
          )}
        </div>
      </div>
    </header>
  );
}
